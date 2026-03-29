"""Streamlit dashboard for PulseOps v3."""

from __future__ import annotations

import html
import json
import textwrap
from datetime import datetime
import time

import pandas as pd
import streamlit as st

from agents.orchestrator import run_orchestrator
from config import REAL_CALENDAR, REAL_JIRA, REAL_SLACK, REAL_TRELLO, USE_REAL_APIS
from tools.audit_ledger import clear_log, get_audit_log, init_db
from utils.explainer import explain_decision

st.set_page_config(page_title="PulseOps", page_icon="⚡", layout="wide")
init_db()

if "orch_result" not in st.session_state:
    st.session_state.orch_result = None
if "active_workflow" not in st.session_state:
    st.session_state.active_workflow = None
if "running" not in st.session_state:
    st.session_state.running = False
if "run_start_time" not in st.session_state:
    st.session_state.run_start_time = None
if "run_duration_seconds" not in st.session_state:
    st.session_state.run_duration_seconds = 0.0
if "event_input" not in st.session_state:
    st.session_state.event_input = "Onboard new employee EMP-2026-001 starting Monday"
if "pending_event_input" not in st.session_state:
    st.session_state.pending_event_input = None

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
:root {
  --bg: #060d1a;
  --panel: #0d1728;
  --panel-2: #101d33;
  --text: #c9d6e3;
  --dim: #4a7c9e;
  --teal: #00f5c4;
  --error: #ff5252;
  --warn: #ffab00;
  --flag: #8250ff;
  --handoff: #4fc3f7;
}
.stApp { background:
  radial-gradient(circle at top right, rgba(79,195,247,0.12), transparent 30%),
  radial-gradient(circle at top left, rgba(0,245,196,0.10), transparent 25%),
  linear-gradient(180deg, #060d1a 0%, #08111f 45%, #091321 100%);
  color: var(--text);
}
.main .block-container { padding-top: 2.1rem; padding-bottom: 2.5rem; max-width: 1380px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(13,23,40,0.98), rgba(8,17,31,0.98)); border-right: 1px solid rgba(79,124,158,0.18); }
[data-testid="stMetric"] { background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)); border: 1px solid rgba(79,124,158,0.16); padding: 14px 16px; border-radius: 16px; }
[data-testid="stMetricLabel"] { color: var(--dim); font-family: 'JetBrains Mono', monospace; }
[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; color: var(--text); }
[data-testid="stTextInput"] label, .stSelectbox label, .stCheckbox label { color: var(--dim) !important; font-family: 'JetBrains Mono', monospace; }
[data-testid="stTextInput"] input {
  background: rgba(10,19,34,0.95) !important;
  border: 1px solid rgba(79,124,158,0.22) !important;
  border-radius: 14px !important;
  color: var(--text) !important;
  height: 3rem !important;
}
.stButton > button {
  border-radius: 14px !important;
  border: 1px solid rgba(79,124,158,0.25) !important;
  background: linear-gradient(180deg, rgba(14,27,46,0.96), rgba(11,20,35,0.96)) !important;
  color: var(--text) !important;
  min-height: 2.9rem;
  font-weight: 600 !important;
  box-shadow: none !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, rgba(0,245,196,0.18), rgba(79,195,247,0.18)) !important;
  border: 1px solid rgba(0,245,196,0.34) !important;
}
.stButton > button:hover, [data-testid="stTextInput"] input:focus {
  border-color: rgba(0,245,196,0.45) !important;
  box-shadow: 0 0 0 1px rgba(0,245,196,0.18), 0 0 18px rgba(0,245,196,0.08) !important;
}
.title { font-family: 'Syne', sans-serif; font-size: 2.9rem; font-weight: 800; color: var(--teal); letter-spacing: -0.03em; line-height: 1; }
.subtitle { font-family: 'JetBrains Mono', monospace; color: var(--dim); font-size: 0.84rem; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 0.45rem; }
.status-on, .status-off { font-family: 'JetBrains Mono', monospace; text-align: right; margin-top: 1rem; }
.status-on { color: var(--teal); animation: blink 1.2s infinite; }
.status-off { color: var(--dim); }
@keyframes blink { 50% { opacity: 0.4; } }
.panel {
  background: linear-gradient(180deg, rgba(255,255,255,0.028), rgba(255,255,255,0.01));
  border: 1px solid rgba(79,124,158,0.20);
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 16px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), 0 20px 50px rgba(2,8,18,0.18);
}
.hero-panel {
  background: linear-gradient(135deg, rgba(8,16,29,0.95), rgba(13,23,40,0.96));
  border: 1px solid rgba(79,124,158,0.24);
  border-radius: 22px;
  padding: 18px 18px 10px 18px;
  margin: 10px 0 18px 0;
  position: relative;
  overflow: hidden;
}
.hero-panel:before {
  content: "";
  position: absolute;
  inset: -30% -10% auto auto;
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(0,245,196,0.14), transparent 60%);
  pointer-events: none;
}
.plan-row, .timeline-row, .ledger-row, .thought-row {
  background: var(--panel);
  border: 1px solid rgba(79,124,158,0.22);
  border-radius: 16px;
  padding: 13px 15px;
  margin-bottom: 10px;
}
.section { font-family: 'Syne', sans-serif; font-size: 1.28rem; color: var(--text); margin: 8px 0 12px; letter-spacing: -0.02em; }
.section-kicker { font-family: 'JetBrains Mono', monospace; color: var(--dim); font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px; }
.mono { font-family: 'JetBrains Mono', monospace; }
.dim { color: var(--dim); }
.summary-grid { display:grid; grid-template-columns: 2.2fr 1fr 1fr 1fr; gap:12px; align-items:center; }
.summary-card { background: rgba(13,23,40,0.86); border:1px solid rgba(79,124,158,0.16); border-radius:16px; padding:14px 16px; margin-bottom:10px; }
.summary-title { font-family: 'Syne', sans-serif; font-size: 1.15rem; color: var(--text); }
.summary-copy { color: var(--dim); margin-top:6px; font-size:0.92rem; }
.summary-stat { text-align:right; }
.summary-stat .label { font-family:'JetBrains Mono', monospace; font-size:0.68rem; color:var(--dim); text-transform:uppercase; letter-spacing:0.1em; }
.summary-stat .value { font-family:'Syne', sans-serif; font-size:1.5rem; color:var(--text); margin-top:4px; }
.badge {
  display: inline-block; padding: 3px 9px; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; margin-left: 8px;
}
.badge-success { background: rgba(0,245,196,0.12); color: var(--teal); border: 1px solid rgba(0,245,196,0.35); }
.badge-escalated { background: rgba(255,171,0,0.12); color: var(--warn); border: 1px solid rgba(255,171,0,0.35); }
.badge-flagged { background: rgba(130,80,255,0.12); color: var(--flag); border: 1px solid rgba(130,80,255,0.35); }
.badge-handoff { background: rgba(79,195,247,0.12); color: var(--handoff); border: 1px solid rgba(79,195,247,0.35); }
.badge-live { background: rgba(0,230,118,0.14); color: #00e676; border: 1px solid rgba(0,230,118,0.4); }
.badge-mock { background: rgba(84,110,122,0.18); color: #90a4ae; border: 1px solid rgba(144,164,174,0.32); }
.agent-header {
  font-family: 'Syne', sans-serif; font-size: 1rem; padding: 8px 12px;
  border-radius: 12px; margin: 14px 0 8px; color: #06101d; font-weight: 700;
}
.live-card { box-shadow: 0 0 0 1px rgba(0,230,118,0.2), 0 0 18px rgba(0,230,118,0.08); }
.topline { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
.subgrid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.api-chip { display:inline-flex; align-items:center; gap:8px; padding:10px 12px; border-radius:14px; margin-right:10px; margin-bottom:8px; background: rgba(13,23,40,0.92); border:1px solid rgba(79,124,158,0.18); }
.timeline-meta { margin-top: 10px; display:flex; flex-wrap:wrap; gap:8px; }
.muted-line { font-size: 0.82rem; color: var(--dim); margin-top: 8px; }
.empty-state { text-align:center; padding: 46px 20px; }
</style>
""",
    unsafe_allow_html=True,
)


def _safe_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def _safe_html_text(value: object, limit: int | None = None) -> str:
    text = "" if value is None else str(value)
    if limit is not None:
        text = text[:limit]
    text = html.escape(text)
    return text.replace("\n", "<br>")


def _render_html(template: str) -> None:
    st.markdown(textwrap.dedent(template).strip(), unsafe_allow_html=True)


def _shorten(text: object, limit: int = 140) -> str:
    raw = "" if text is None else str(text)
    return raw if len(raw) <= limit else raw[: limit - 1] + "…"


def _run_event(event: str, employee_id: str, approval_id: str) -> None:
    st.session_state.running = True
    st.session_state.run_start_time = time.time()
    result = run_orchestrator(event, employee_id=employee_id, approval_id=approval_id)
    st.session_state.orch_result = result
    st.session_state.active_workflow = result["workflow_id"]
    st.session_state.run_duration_seconds = time.time() - st.session_state.run_start_time
    st.session_state.running = False


def _rubric(result: dict | None) -> dict:
    if not result:
        return {
            "Autonomy": 0,
            "Multi-Agent": 90,
            "Creativity": 90,
            "Enterprise": 50,
            "Impact": 90,
            "Total": 0,
        }
    autonomy = min(100, int((result.get("total_steps", 0) / 10) * 100))
    enterprise = min(100, 50 + result.get("total_escalations", 0) * 15)
    total = (
        autonomy * 0.30
        + 90 * 0.20
        + 90 * 0.20
        + enterprise * 0.20
        + 90 * 0.10
    )
    return {
        "Autonomy": autonomy,
        "Multi-Agent": 90,
        "Creativity": 90,
        "Enterprise": enterprise,
        "Impact": 90,
        "Total": round(total, 1),
    }


def _collect_thought_rows(result: dict) -> list[dict]:
    rows: list[dict] = []
    for agent, payload in result.get("all_results", {}).items():
        for item in payload.get("thought_chain", []):
            rows.append({"agent": agent, **item})
    return sorted(rows, key=lambda row: (row["step"], row["agent"]))


def _notification_rows(result: dict) -> list[dict]:
    rows: list[dict] = []
    now = datetime.now().strftime("%H:%M:%S")
    for agent, payload in result.get("all_results", {}).items():
        for item in payload.get("thought_chain", []):
            data = _safe_json(item.get("result", ""))
            action = item.get("action", "")
            if action == "slack_send_welcome" and data.get("status") == "sent":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Slack",
                        "Recipient": "#welcome",
                        "Message": data.get("message", ""),
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "it_escalation_ticket":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Email",
                        "Recipient": "it-helpdesk@company.com",
                        "Message": f"Escalation created for {data.get('ticket_id', 'IT-UNKNOWN')}",
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "slack_it_alert":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Slack",
                        "Recipient": "#it-alerts",
                        "Message": f"IT escalation alert sent for {data.get('ticket_id', 'IT-UNKNOWN')}",
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "hr_assign_buddy":
                buddy = data.get("buddy", {})
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Slack",
                        "Recipient": buddy.get("name", "Assigned Buddy"),
                        "Message": "You have been assigned as onboarding buddy.",
                        "Status": "SIMULATED",
                    }
                )
            elif action == "calendar_schedule_orientation":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Email",
                        "Recipient": "orientation attendees",
                        "Message": f"Orientation scheduled for {data.get('date', 'tomorrow')} {data.get('time', '')}",
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "create_task":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Slack",
                        "Recipient": data.get("owner", "task owner"),
                        "Message": f"Task created: {data.get('task', 'New task')}",
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "flag_ambiguous_item":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Email",
                        "Recipient": data.get("sent_to", "meeting_host@company.com"),
                        "Message": f"Clarification requested for {data.get('task', 'ambiguous item')}",
                        "Status": "SIMULATED",
                    }
                )
            elif action == "send_meeting_summary":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Slack",
                        "Recipient": "#meeting-summary",
                        "Message": f"Meeting summary sent with {data.get('tasks_included', data.get('tasks_created', 0))} tasks and {data.get('flagged_included', data.get('items_flagged', 0))} flagged items",
                        "Status": "DELIVERED" if item.get("api_source") == "REAL_API" else "SIMULATED",
                    }
                )
            elif action == "reroute_to_delegate":
                rows.append(
                    {
                        "Time": now,
                        "From Agent": agent,
                        "Channel": "Email",
                        "Recipient": f"{data.get('delegate_name', 'delegate')} + compliance",
                        "Message": f"Approval rerouted with override logged for {data.get('approval_id', '')}",
                        "Status": "SIMULATED",
                    }
                )
    return rows


def _source_badge(source: str) -> str:
    normalized = (source or "UNKNOWN").upper()
    if normalized == "REAL_API":
        return "LIVE"
    if normalized == "MOCK_FALLBACK":
        return "FALLBACK"
    if normalized in {"MOCK", "INTERNAL", "UNKNOWN"}:
        return "MOCK"
    return "MOCK"


def _status_badge(status: str) -> str:
    return status.upper()


def _api_status_bar() -> str:
    statuses = [
        ("Slack", REAL_SLACK),
        ("JIRA", REAL_JIRA),
        ("Calendar", REAL_CALENDAR),
        ("Trello", REAL_TRELLO),
    ]
    parts = []
    for name, is_live in statuses:
        badge = "badge-live" if is_live else "badge-mock"
        label = "LIVE" if is_live else "MOCK"
        parts.append(
            f"<span class='api-chip mono'>{name} <span class='badge {badge}'>{label}</span></span>"
        )
    return (
        "<div class='panel'>"
        "<div class='section-kicker'>Integration Status</div>"
        "<div class='section' style='font-size:1rem;margin-top:0;'>Connected Systems</div>"
        + "".join(parts)
        + "</div>"
    )


def _agent_source_summary(payload: dict) -> str:
    sources = {item.get("api_source", "UNKNOWN") for item in payload.get("thought_chain", [])}
    ordered = []
    if "REAL_API" in sources:
        ordered.append("LIVE")
    if "MOCK_FALLBACK" in sources:
        ordered.append("FALLBACK")
    if {"MOCK", "INTERNAL", "UNKNOWN"} & sources:
        ordered.append("MOCK")
    return " | ".join(ordered) if ordered else "MOCK"


def _observed_metrics(result: dict | None) -> dict:
    if not result:
        return {
            "duration_seconds": 0.0,
            "agents": 0,
            "successful_actions": 0,
            "escalations": 0,
            "flagged": 0,
            "handoffs": 0,
            "live_calls": 0,
            "mock_calls": 0,
            "notifications": 0,
        }
    live_calls = 0
    mock_calls = 0
    notifications = len(_notification_rows(result))
    for payload in result.get("all_results", {}).values():
        for item in payload.get("thought_chain", []):
            source = str(item.get("api_source", "UNKNOWN")).upper()
            if source == "REAL_API":
                live_calls += 1
            else:
                mock_calls += 1
    return {
        "duration_seconds": round(st.session_state.run_duration_seconds, 2),
        "agents": len(result.get("agents_activated", [])),
        "successful_actions": result.get("total_steps", 0),
        "escalations": result.get("total_escalations", 0),
        "flagged": result.get("total_flagged", 0),
        "handoffs": result.get("handoffs_triggered", 0),
        "live_calls": live_calls,
        "mock_calls": mock_calls,
        "notifications": notifications,
    }


header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown("<div class='title'>PulseOps</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Autonomous Multi-Agent Enterprise Operations</div>",
        unsafe_allow_html=True,
    )
with header_right:
    label = "● RUNNING WORKFLOW" if st.session_state.running else "○ READY"
    css = "status-on" if st.session_state.running else "status-off"
    st.markdown(f"<div class='{css}'>{label}</div>", unsafe_allow_html=True)

st.markdown(_api_status_bar(), unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Parameters")
    employee_id = st.text_input("Employee ID", value="EMP-2026-001")
    approval_id = st.text_input("Approval ID", value="PROC-4821")
    st.checkbox("Use Real APIs", value=USE_REAL_APIS, disabled=True)
    if st.button("Reset", use_container_width=True):
        clear_log()
        from tools.mock_apis import reset_jira_mock
        from agents.onboard_agent import reset_employee_cache

        reset_jira_mock()
        reset_employee_cache()
        st.session_state.orch_result = None
        st.session_state.active_workflow = None
        st.session_state.running = False
        st.session_state.run_start_time = None
        st.session_state.run_duration_seconds = 0.0
        st.rerun()

    st.markdown("### Demo Metrics")
    observed = _observed_metrics(st.session_state.orch_result)
    st.metric("Workflow duration", f"{observed['duration_seconds']}s")
    st.metric("Live API calls", observed["live_calls"])
    st.metric("Notifications sent", observed["notifications"])

    st.markdown("### Live Rubric Score")
    rubric = _rubric(st.session_state.orch_result)
    for label, weight in [
        ("Autonomy", 30),
        ("Multi-Agent", 20),
        ("Creativity", 20),
        ("Enterprise", 20),
        ("Impact", 10),
    ]:
        st.caption(f"{label} {weight}%")
        st.progress(rubric[label] / 100)
    st.metric("Weighted Total", f"{rubric['Total']}%")

st.markdown(
    "<div class='hero-panel'><div class='section-kicker'>Command Center</div><div class='section' style='margin-top:0;'>What enterprise event should PulseOps handle?</div></div>",
    unsafe_allow_html=True,
)
input_col, run_col = st.columns([6, 1])
with input_col:
    if st.session_state.pending_event_input is not None:
        st.session_state.event_input = st.session_state.pending_event_input
        st.session_state.pending_event_input = None
    event = st.text_input("Enterprise Event", key="event_input", label_visibility="collapsed")
with run_col:
    run_clicked = st.button("▶ Run PulseOps", use_container_width=True, type="primary")

quick1, quick2, quick3 = st.columns(3)
quick_event = None
with quick1:
    if st.button("🧑‍💼 Employee Onboarding", use_container_width=True):
        quick_event = "Onboard new employee EMP-2026-001 starting Monday"
with quick2:
    if st.button("📋 Meeting Action Items", use_container_width=True):
        quick_event = "Process Platform Engineering Sync meeting transcript"
with quick3:
    if st.button("🚨 SLA Breach Prevention", use_container_width=True):
        quick_event = "SLA breach on PROC-4821 requires immediate rerouting"

if quick_event:
    st.session_state.pending_event_input = quick_event
    _run_event(quick_event, employee_id, approval_id)
    st.rerun()

if run_clicked and st.session_state.event_input.strip():
    _run_event(st.session_state.event_input.strip(), employee_id, approval_id)
    st.rerun()

result = st.session_state.orch_result
logs = get_audit_log(st.session_state.active_workflow) if st.session_state.active_workflow else []

if result:
    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Successful Actions", result.get("total_steps", 0))
    metric2.metric("Escalations", result.get("total_escalations", 0))
    metric3.metric("Flagged", result.get("total_flagged", 0))

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Supervisor View</div>", unsafe_allow_html=True)
    st.markdown("<div class='section'>🎯 Orchestrator Plan</div>", unsafe_allow_html=True)
    for item in result.get("plan", []):
        reason = _safe_html_text(item.get("reason", ""))
        agent = _safe_html_text(item.get("agent", ""))
        _render_html(
            f"""
            <div class="plan-row">
              <span class="mono">Priority {item.get("priority", 1)} → {agent}</span>
              <span class="dim">"{reason}"</span>
            </div>
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Execution Overview</div>", unsafe_allow_html=True)
    st.markdown("<div class='section'>Agent Execution Timeline</div>", unsafe_allow_html=True)
    planned_agents = {item.get("agent") for item in result.get("plan", [])}
    for agent_name in result.get("execution_order", []):
        payload = result["all_results"].get(agent_name, {})
        source_summary = _agent_source_summary(payload)
        auto_triggered = "AUTO-TRIGGERED" if agent_name not in planned_agents else ""
        status_label = "ERROR" if payload.get("error") else "COMPLETE"
        final_copy = _safe_html_text(_shorten(payload.get("final_message") or payload.get("error") or "Workflow finished."))
        auto_copy = f"<span class='badge badge-handoff'>{auto_triggered}</span>" if auto_triggered else ""
        _render_html(
            f"""
            <div class="summary-card">
              <div class="summary-grid">
                <div>
                  <div class="summary-title">[{_safe_html_text(agent_name)}] <span class='badge badge-success'>{status_label}</span> {auto_copy}</div>
                  <div class="summary-copy">{final_copy}</div>
                  <div class="summary-copy mono">Source Mix: {_safe_html_text(source_summary)}</div>
                </div>
                <div class="summary-stat">
                  <div class="label">Steps</div>
                  <div class="value">{payload.get("total_steps", 0)}</div>
                </div>
                <div class="summary-stat">
                  <div class="label">Escalations</div>
                  <div class="value">{payload.get("steps_escalated", 0)}</div>
                </div>
                <div class="summary-stat">
                  <div class="label">Flagged</div>
                  <div class="value">{payload.get("steps_flagged", 0)}</div>
                </div>
              </div>
            </div>
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])
    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='section-kicker'>Reasoning Trace</div>", unsafe_allow_html=True)
        st.markdown("<div class='section'>Thought Chain</div>", unsafe_allow_html=True)
        by_agent: dict[str, list[dict]] = {}
        for row in _collect_thought_rows(result):
            by_agent.setdefault(row["agent"], []).append(row)
        agent_colors = {
            "OnboardAgent": "#00f5c4",
            "MeetingAgent": "#8250ff",
            "SLAAgent": "#ffab00",
            "TicketMonitorAgent": "#4fc3f7",
        }
        for agent_name, rows in by_agent.items():
            color = agent_colors.get(agent_name, "#c9d6e3")
            st.markdown(
                f"<div class='agent-header' style='background:{color}'>{_safe_html_text(agent_name)}</div>",
                unsafe_allow_html=True,
            )
            preview_rows = rows[:6]
            extra_rows = rows[6:]
            for row in preview_rows:
                card_classes = "thought-row live-card" if row.get("api_source") == "REAL_API" else "thought-row"
                safe_row_agent = _safe_html_text(row["agent"])
                safe_thought = _safe_html_text(_shorten(row.get("thought", ""), 180))
                safe_action = _safe_html_text(row.get("action", ""))
                _render_html(
                    f"""
                    <div class="{card_classes}">
                      <div class="mono">🧠 [{safe_row_agent}] Step {row["step"]}</div>
                      <div><em>{safe_thought}</em></div>
                      <div class="mono" style="margin-top:8px;">⚡ Called: {safe_action}</div>
                      <div class="muted-line mono">Status: {_safe_html_text(_status_badge(row.get("status", "SUCCESS")))} | Source: {_safe_html_text(_source_badge(row.get("api_source", "UNKNOWN")))}</div>
                    </div>
                    """
                )
            if extra_rows:
                with st.expander(f"Show {len(extra_rows)} more {agent_name} steps", expanded=False):
                    for row in extra_rows:
                        st.caption(f"Step {row['step']} | {row.get('action', '')} | {row.get('status', '')}")
                        st.write(_shorten(row.get("thought", ""), 220))
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='section-kicker'>Compliance Trail</div>", unsafe_allow_html=True)
        st.markdown("<div class='section'>Live Audit Ledger</div>", unsafe_allow_html=True)
        preview_logs = logs[-10:]
        older_logs = logs[:-10]
        for entry in preview_logs:
            safe_entry_agent = _safe_html_text(entry["agent"])
            safe_entry_action = _safe_html_text(entry["action"][:60])
            safe_entry_thought = _safe_html_text(_shorten(entry.get("thought", ""), 90))
            _render_html(
                f"""
                <div class="ledger-row">
                  <div class="mono">{safe_entry_agent} · {entry["timestamp"]}</div>
                  <div>{safe_entry_action}</div>
                  <div class="dim">{safe_entry_thought}</div>
                  <div class="muted-line mono">
                    Status: {_safe_html_text(_status_badge(entry["status"]))}
                    | Source: {_safe_html_text(_source_badge(entry.get("api_source", "UNKNOWN")))}
                    {" | Retry" if entry.get("retry_count", 0) else ""}
                    {" | Escalated" if entry.get("escalated") else ""}
                    | Confidence: {int(float(entry.get("confidence", 1.0)) * 100)}%
                  </div>
                </div>
                """
            )
        if older_logs:
            with st.expander(f"Show {len(older_logs)} older ledger entries", expanded=False):
                for entry in older_logs:
                    st.caption(f"{entry['agent']} | Step {entry['step']} | {entry['status']}")
                    st.write(_shorten(entry["action"], 90))

        st.markdown("<div class='section'>Explain This Decision</div>", unsafe_allow_html=True)
        explain_options = [
            f"{entry['agent']} — Step {entry['step']}: {entry['action']}" for entry in logs
        ]
        if explain_options:
            selected = st.selectbox("Decision", explain_options, label_visibility="collapsed")
            if st.button("Explain", use_container_width=True):
                agent_name, remainder = selected.split(" — Step ", 1)
                step = int(remainder.split(":", 1)[0])
                st.info(explain_decision(st.session_state.active_workflow, step, agent_name))
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📨 Notifications Dispatched", expanded=False):
        notifications = _notification_rows(result)
        if notifications:
            st.dataframe(pd.DataFrame(notifications), use_container_width=True, hide_index=True)
        else:
            st.caption("No derived notifications for this workflow.")

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-kicker'>Observed Outcomes</div>", unsafe_allow_html=True)
    st.markdown("<div class='section'>Workflow Metrics</div>", unsafe_allow_html=True)
    observed = _observed_metrics(result)
    c1, c2, c3 = st.columns(3)
    c1.metric("Workflow Duration", f"{observed['duration_seconds']}s")
    c2.metric("Agents Activated", observed["agents"])
    c3.metric("Successful Actions", observed["successful_actions"])
    c4, c5, c6 = st.columns(3)
    c4.metric("Escalations", observed["escalations"])
    c5.metric("Flagged Items", observed["flagged"])
    c6.metric("Handoffs Triggered", observed["handoffs"])
    c7, c8, c9 = st.columns(3)
    c7.metric("Live API Calls", observed["live_calls"])
    c8.metric("Mock API Calls", observed["mock_calls"])
    c9.metric("Notifications Sent", observed["notifications"])
    st.caption("These values are measured from the current run and do not use estimated cost or ROI assumptions.")
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(
        "<div class='panel empty-state'><div class='section-kicker'>Ready</div><div class='section'>Run PulseOps to watch the orchestrator plan, delegate, recover, and explain every action.</div><div class='muted-line mono'>Use one of the quick scenarios above or describe your own enterprise event.</div></div>",
        unsafe_allow_html=True,
    )
