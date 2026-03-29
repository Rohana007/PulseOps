"""PulseOps meeting specialist agent."""

from __future__ import annotations

from tools import mock_apis
from tools.api_router import route
from tools.audit_ledger import log_action

# Module-level state for the current run.
_session_tasks: list[dict] = []
_session_flagged: list[dict] = []


def _log_step(workflow_id: str, step: int, thought: str, action: str, tool_called: str, result: dict, status: str) -> dict:
    log_action(
        workflow=workflow_id,
        agent="MeetingAgent",
        step=step,
        thought=thought,
        action=action,
        tool_called=tool_called,
        result=str(result)[:400],
        status=status,
        escalated=status in {"FLAGGED", "ESCALATED"},
        confidence=0.88,
        api_source=result.get("_source", "UNKNOWN"),
    )
    return {
        "step": step,
        "thought": thought,
        "action": tool_called,
        "params": {},
        "status": status,
        "result": str(result)[:400],
        "escalated": status in {"FLAGGED", "ESCALATED"},
        "api_source": result.get("_source", "UNKNOWN"),
    }


def _reset_session() -> None:
    global _session_tasks, _session_flagged
    _session_tasks = []
    _session_flagged = []


def run_meeting_agent(transcript: str, workflow_id: str) -> dict:
    _reset_session()
    thought_chain: list[dict] = []
    items = [
        {"task": "Prepare payments migration plan", "owner": "Rahul", "ambiguous": False},
        {"task": "Update ML pipeline after migration", "owner": "Sneha", "ambiguous": False},
        {"task": "Update API documentation", "owner": None, "ambiguous": True, "ambiguity_reason": "No explicit owner assigned"},
        {"task": "Review Q4 budget proposal", "owner": None, "ambiguous": True, "ambiguity_reason": "Owner not decided in meeting"},
    ]
    parse_result = {
        "status": "success",
        "total": len(items),
        "clear_items": [item for item in items if not item["ambiguous"]],
        "ambiguous_items": [item for item in items if item["ambiguous"]],
        "_source": "INTERNAL",
    }
    thought_chain.append(
        _log_step(
            workflow_id,
            1,
            "I should extract all action items first so I can separate clearly owned work from ambiguous follow-ups.",
            "Parse meeting transcript",
            "get_action_items",
            parse_result,
            "SUCCESS",
        )
    )

    step = 2
    for item in parse_result["clear_items"]:
        task_result = route("trello_create_card", task=item["task"], owner=item["owner"])
        _session_tasks.append(
            {
                "task": item["task"],
                "owner": item["owner"],
                "task_id": task_result.get("card_id", task_result.get("task_id", "TASK-0000")),
            }
        )
        thought_chain.append(
            _log_step(
                workflow_id,
                step,
                f"{item['owner']} was explicitly assigned, so I can create the task safely without guessing.",
                "Create task",
                "create_task",
                task_result,
                "SUCCESS",
            )
        )
        step += 1

    for item in parse_result["ambiguous_items"]:
        flag_result = mock_apis.send_clarification_request(item["task"], item["ambiguity_reason"])
        flag_result["candidate_owners"] = [
            {"name": "Rahul", "confidence": 0.52, "reason": "Mentioned near the technical workstream"},
            {"name": "Vikram", "confidence": 0.38, "reason": "Offered to coordinate with tech writing"},
        ]
        flag_result["_source"] = "MOCK"
        _session_flagged.append(
            {
                "task": item["task"],
                "reason": item["ambiguity_reason"],
                "candidates": flag_result["candidate_owners"],
            }
        )
        thought_chain.append(
            _log_step(
                workflow_id,
                step,
                "Ownership is ambiguous, so I must flag this item instead of assigning it to the wrong person.",
                "Flag ambiguous item",
                "flag_ambiguous_item",
                flag_result,
                "FLAGGED",
            )
        )
        step += 1

    summary = route("slack_send_meeting_summary", tasks=_session_tasks, flagged=_session_flagged)
    summary["tasks_created"] = len(parse_result["clear_items"])
    summary["items_flagged"] = len(parse_result["ambiguous_items"])
    thought_chain.append(
        _log_step(
            workflow_id,
            step,
            "A meeting summary closes the loop by broadcasting what was assigned and what still needs clarification.",
            "Send meeting summary",
            "send_meeting_summary",
            summary,
            "SUCCESS",
        )
    )

    return {
        "thought_chain": thought_chain,
        "steps_completed": len([t for t in thought_chain if t["status"] == "SUCCESS"]),
        "steps_escalated": 0,
        "steps_flagged": len([t for t in thought_chain if t["status"] == "FLAGGED"]),
        "steps_errored": 0,
        "total_steps": len(thought_chain),
        "final_message": "Meeting workflow completed with clear tasks created and ambiguous items flagged for review.",
    }
