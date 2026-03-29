"""
LangGraph workflow: ingest → scenario router → specialist agents → follow-ups → finalize.

- Ingest normalizes trace start.
- Conditional routing dispatches to onboarding, meeting, SLA, or unknown.
- Meeting path adds a follow-up node when policies require human clarification.
- Finalize attaches _graph_trace for the dashboard / auditability.
- MemorySaver checkpointing enables inspectable thread state per workflow_id.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agents.meeting_agent import extract_action_items
from agents.onboard_agent import run_onboarding
from agents.sla_agent import run_sla_check
from tools.audit_ledger import log_action
from tools.mock_apis import get_meeting_transcript

_checkpointer: MemorySaver | None = None


def _get_checkpointer() -> MemorySaver:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def _ingest(state: dict) -> dict:
    # LangGraph dict channels replace the whole state per update; merge so routing keeps inputs.
    return {**state, "trace": ["ingest"]}


def _route_after_ingest(state: dict) -> str:
    label = state.get("scenario", "") or ""
    if "Onboarding" in label:
        return "onboard_specialist"
    if "Meeting" in label:
        return "meeting_specialist"
    if "SLA" in label:
        return "sla_specialist"
    return "unknown_handler"


def _onboard_specialist(state: dict) -> dict:
    wf = state["workflow_id"]
    emp = state.get("employee_id", "EMP-2026-001")
    data = run_onboarding(emp, wf)
    trace = list(state.get("trace", [])) + ["onboard_specialist"]
    return {**state, "result": {"type": "onboarding", "data": data}, "trace": trace}


def _meeting_specialist(state: dict) -> dict:
    wf = state["workflow_id"]
    transcript = get_meeting_transcript()
    data = extract_action_items(transcript, wf)
    trace = list(state.get("trace", [])) + ["meeting_specialist"]
    return {**state, "result": {"type": "meeting", "data": data}, "trace": trace}


def _meeting_followup(state: dict) -> dict:
    """
    Post-meeting policy node: do not auto-assign ambiguous work; log orchestration policy.
    Always runs after meeting_specialist (cheap no-op when nothing is flagged).
    """
    res = state.get("result") or {}
    data = res.get("data") or {}
    trace = list(state.get("trace", [])) + ["meeting_followup"]

    flagged = data.get("flagged_items") or []
    if flagged:
        log_action(
            workflow=state["workflow_id"],
            agent="PulseGraph",
            step=7,
            action="Orchestration policy: ambiguous action items held human-in-the-loop",
            tool_called="graph.meeting_followup",
            result=f"{len(flagged)} item(s) flagged; no auto-assignment per policy",
            status="PARTIAL",
            reasoning=(
                "Meeting agent completed deterministic task creation for clear owners; "
                "graph layer records that ambiguous items stay in clarification queue."
            ),
        )
        trace = trace + ["policy_human_clarification"]

    return {**state, "trace": trace}


def _sla_specialist(state: dict) -> dict:
    wf = state["workflow_id"]
    approval_id = state.get("approval_id", "PROC-4821")
    data = run_sla_check(approval_id, wf)
    trace = list(state.get("trace", [])) + ["sla_specialist"]
    return {**state, "result": {"type": "sla", "data": data}, "trace": trace}


def _unknown_handler(state: dict) -> dict:
    trace = list(state.get("trace", [])) + ["unknown_handler"]
    return {
        **state,
        "result": {"type": "unknown", "data": None, "error": "Unknown scenario"},
        "trace": trace,
    }


def _finalize(state: dict) -> dict:
    r = state.get("result")
    if not isinstance(r, dict):
        r = {"type": "unknown", "data": None, "error": "No result produced"}
    out = {**r, "_graph_trace": list(state.get("trace", [])) + ["finalize"]}
    return {**state, "result": out}


def build_workflow_app():
    graph = StateGraph(dict)
    graph.add_node("ingest", _ingest)
    graph.add_node("onboard_specialist", _onboard_specialist)
    graph.add_node("meeting_specialist", _meeting_specialist)
    graph.add_node("meeting_followup", _meeting_followup)
    graph.add_node("sla_specialist", _sla_specialist)
    graph.add_node("unknown_handler", _unknown_handler)
    graph.add_node("finalize", _finalize)

    graph.set_entry_point("ingest")
    graph.add_conditional_edges(
        "ingest",
        _route_after_ingest,
        {
            "onboard_specialist": "onboard_specialist",
            "meeting_specialist": "meeting_specialist",
            "sla_specialist": "sla_specialist",
            "unknown_handler": "unknown_handler",
        },
    )

    graph.add_edge("onboard_specialist", "finalize")
    graph.add_edge("sla_specialist", "finalize")
    graph.add_edge("unknown_handler", "finalize")
    graph.add_edge("meeting_specialist", "meeting_followup")
    graph.add_edge("meeting_followup", "finalize")

    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=_get_checkpointer())
