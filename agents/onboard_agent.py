"""PulseOps onboarding specialist agent."""

from __future__ import annotations

from datetime import datetime, timedelta

from tools import mock_apis
from tools.api_router import route
from tools.audit_ledger import log_action

_employee_cache: dict[str, dict] = {}


def _with_source(payload: dict, source: str = "MOCK") -> dict:
    payload["_source"] = source
    return payload


def _log_step(
    workflow_id: str,
    step: int,
    thought: str,
    action: str,
    tool_called: str,
    result: dict,
    status_override: str | None = None,
    retry_count: int = 0,
) -> dict:
    status = status_override or "SUCCESS"
    raw = str(result).lower()
    if status_override is None and result.get("status") == "error":
        status = "ERROR"
    elif status_override is None and ("ticket_created" in raw or "rerouted" in raw):
        status = "ESCALATED"
    log_action(
        workflow=workflow_id,
        agent="OnboardAgent",
        step=step,
        thought=thought,
        action=action,
        tool_called=tool_called,
        result=str(result)[:400],
        status=status,
        escalated=status == "ESCALATED",
        retry_count=retry_count,
        confidence=0.9,
        api_source=result.get("_source", "UNKNOWN"),
    )
    return {
        "step": step,
        "thought": thought,
        "action": tool_called,
        "params": {},
        "status": status,
        "result": str(result)[:400],
        "escalated": status == "ESCALATED",
        "api_source": result.get("_source", "UNKNOWN"),
        "retry_count": retry_count,
    }


def reset_employee_cache() -> None:
    global _employee_cache
    _employee_cache = {}


def run_onboarding(employee_id: str, workflow_id: str) -> dict:
    reset_employee_cache()
    thought_chain: list[dict] = []

    employee = route("hr_get_employee", employee_id=employee_id)
    if employee.get("status") == "success" or "name" in employee:
        _employee_cache[employee_id] = employee
    thought_chain.append(
        _log_step(
            workflow_id,
            1,
            "I need the employee profile first so every downstream provisioning step uses the right role, team, and manager context.",
            "Fetch employee profile",
            "hr_get_employee",
            employee,
        )
    )

    gsuite = _with_source(mock_apis.gsuite_create_account(employee_id, employee.get("role", "Employee")))
    thought_chain.append(
        _log_step(
            workflow_id,
            2,
            "Google Workspace access is foundational for email and day-one collaboration, so I should provision it early.",
            "Create Google Workspace account",
            "gsuite_create_account",
            gsuite,
        )
    )

    slack = _with_source(mock_apis.slack_create_account(employee_id, employee.get("team", "General")))
    thought_chain.append(
        _log_step(
            workflow_id,
            3,
            "Slack is the primary communication channel, so creating it next reduces onboarding friction immediately.",
            "Create Slack account",
            "slack_create_account",
            slack,
        )
    )

    jira_first = route(
        "jira_create_user",
        employee_email=f"{employee_id.lower()}@company.com",
        display_name=employee_id,
    )
    if jira_first.get("status") == "error":
        thought_chain.append(
            _log_step(
                workflow_id,
                4,
                "JIRA failed on the first attempt, so I should retry once before escalating per policy.",
                "Retry JIRA account creation",
                "jira_create_account",
                jira_first,
                status_override="RETRY",
                retry_count=1,
            )
        )
        jira_second = route(
            "jira_create_user",
            employee_email=f"{employee_id.lower()}@company.com",
            display_name=employee_id,
        )
        if jira_second.get("status") == "error":
            jira_result = route(
                "jira_create_ticket",
                project_key="IT",
                summary=f"Provisioning failed: {employee_id}",
                description="JIRA provisioning failed after one retry.",
                issue_type="Bug",
            )
            ticket_id = jira_result.get("ticket_id", f"IT-{employee_id}")
            alert_result = route(
                "slack_it_alert",
                ticket_id=ticket_id,
                employee_id=employee_id,
                error="JIRA provisioning failed after one retry.",
            )
            jira_result["slack_notified"] = alert_result.get("status") == "sent"
            thought_chain.append(
                _log_step(
                    workflow_id,
                    5,
                    "The retry also failed, so I must escalate to IT and continue with the remaining onboarding tasks.",
                    "Escalate JIRA failure",
                    "it_escalation_ticket",
                    jira_result,
                )
            )
            thought_chain.append(
                _log_step(
                    workflow_id,
                    6,
                    "IT should be alerted immediately so the provisioning issue is visible while onboarding continues.",
                    "Send IT Slack alert",
                    "slack_it_alert",
                    alert_result,
                )
            )
        else:
            jira_result = jira_second
            thought_chain.append(
                _log_step(
                    workflow_id,
                    5,
                    "The retry succeeded, so onboarding can continue without escalation.",
                    "Create JIRA account",
                    "jira_create_account",
                    jira_result,
                )
            )
    else:
        jira_result = jira_first
        thought_chain.append(
            _log_step(
                workflow_id,
                4,
                "JIRA succeeded on the first try, so I can continue to the remaining people-ops tasks.",
                "Create JIRA account",
                "jira_create_account",
                jira_result,
            )
        )

    buddy = _with_source(mock_apis.hr_assign_buddy(employee.get("team", "General")))
    thought_chain.append(
        _log_step(
            workflow_id,
            7,
            "Assigning a buddy makes day-one support immediate and improves the new-hire experience.",
            "Assign onboarding buddy",
            "hr_assign_buddy",
            buddy,
        )
    )

    tomorrow = (
        datetime.now() + timedelta(days=1)
    ).replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    orientation = route(
        "calendar_create_event",
        summary=f"New Hire Orientation - {employee_id}",
        attendee_emails=[
            _employee_cache.get(employee_id, {}).get("email", f"{employee_id.lower()}@company.com"),
            "hr@company.com",
        ],
        start_datetime=tomorrow,
        duration_minutes=60,
    )
    thought_chain.append(
        _log_step(
            workflow_id,
            8,
            "Scheduling orientation now ensures the employee has a structured first-day plan.",
            "Schedule orientation",
            "calendar_schedule_orientation",
            orientation,
        )
    )

    welcome = route(
        "slack_send_welcome",
        employee_name=employee.get("name", employee_id),
        employee_email=_employee_cache.get(employee_id, {}).get(
            "email", f"{employee_id.lower()}@company.com"
        ),
    )
    thought_chain.append(
        _log_step(
            workflow_id,
            9,
            "A welcome message closes the loop and gives the new hire the next actions in a friendly way.",
            "Send welcome message",
            "slack_send_welcome",
            welcome,
        )
    )

    return {
        "thought_chain": thought_chain,
        "steps_completed": len([t for t in thought_chain if t["status"] == "SUCCESS"]),
        "steps_escalated": len([t for t in thought_chain if t["status"] in {"ESCALATED", "ERROR"}]),
        "steps_flagged": 0,
        "steps_errored": len([t for t in thought_chain if t["status"] == "ERROR"]),
        "total_steps": len(thought_chain),
        "final_message": "Onboarding workflow completed with recovery logic applied where needed.",
    }
