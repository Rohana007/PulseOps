"""Route tool calls to real APIs or mock fallbacks."""

from __future__ import annotations

from config import REAL_CALENDAR, REAL_JIRA, REAL_SHEETS, REAL_SLACK, REAL_TRELLO
from tools import mock_apis, real_apis


def route(tool_name: str, workflow_id: str | None = None, **kwargs) -> dict:
    """Route a named tool call to real or mock implementation with graceful fallback."""
    real_fn = None
    mock_fn = None
    using_real = False

    if tool_name == "slack_send_welcome":
        if REAL_SLACK:
            real_fn = real_apis.slack_send_welcome_real
            using_real = True
        mock_fn = lambda employee_name, employee_email=None, **kw: mock_apis.slack_send_welcome(
            employee_name
        )
    elif tool_name == "slack_it_alert":
        if REAL_SLACK:
            real_fn = real_apis.slack_send_it_alert_real
            using_real = True
        mock_fn = lambda **kw: {"status": "sent", "channel": "#it-alerts"}
    elif tool_name == "slack_send_meeting_summary":
        if REAL_SLACK:
            real_fn = real_apis.slack_send_meeting_summary_real
            using_real = True
        mock_fn = lambda **kw: {"status": "sent", "channel": "#platform-eng"}
    elif tool_name == "jira_create_user":
        if REAL_JIRA:
            real_fn = real_apis.jira_create_user_real
            using_real = True
        mock_fn = lambda employee_email, display_name: mock_apis.jira_create_account(
            employee_email.split("@")[0].upper()
        )
    elif tool_name == "jira_create_ticket":
        if REAL_JIRA:
            real_fn = real_apis.jira_create_ticket_real
            using_real = True
        mock_fn = lambda summary, description, project_key="IT", issue_type="Task", **kw: mock_apis.it_escalation_ticket(
            summary.replace("Provisioning failed: ", ""),
            description,
        )
    elif tool_name == "calendar_create_event":
        if REAL_CALENDAR:
            real_fn = real_apis.calendar_create_event_real
            using_real = True
        mock_fn = (
            lambda summary, attendee_emails, start_datetime, duration_minutes=60, **kw: mock_apis.calendar_schedule_orientation(
                attendee_emails[0].split("@")[0].upper(),
                "Arjun Mehta",
            )
        )
    elif tool_name == "hr_get_employee":
        if REAL_SHEETS:
            real_fn = real_apis.sheets_get_employee_real
            using_real = True
        mock_fn = mock_apis.hr_get_employee
    elif tool_name == "trello_create_card":
        if REAL_TRELLO:
            real_fn = real_apis.trello_create_card_real
            using_real = True
        mock_fn = mock_apis.project_tracker_create_task

    if using_real and real_fn:
        try:
            result = real_fn(**kwargs)
            if result.get("status") == "error":
                raise RuntimeError(result.get("message", "Real API error"))
            result["_source"] = "REAL_API"
            return result
        except Exception as exc:
            if mock_fn:
                result = mock_fn(**kwargs)
                result["_source"] = "MOCK_FALLBACK"
                result["_fallback_reason"] = str(exc)
                return result
            return {"status": "error", "message": str(exc), "_source": "ERROR"}

    if mock_fn:
        result = mock_fn(**kwargs)
        result["_source"] = "MOCK"
        return result

    return {"status": "error", "message": f"No handler for tool: {tool_name}", "_source": "ERROR"}
