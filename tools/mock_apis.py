"""Mock enterprise APIs for the PulseOps v3 demo."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

_jira_call_counts: dict[str, int] = {}

SAMPLE_TRANSCRIPT = """
Meeting: Platform Engineering Sync
Attendees: Arjun (EM), Rahul (Backend), Sneha (Data), Vikram (Product)

Arjun: We need to migrate the payments database by end of month.
  Rahul, can you lead the migration plan?
Rahul: Sure. I will have a draft ready by Thursday.
Arjun: Sneha, can you update the ML pipeline once Rahul migration is done?
Sneha: Will do.
Arjun: We also need someone to update the API documentation.
  No clear owner yet.
Vikram: I can flag this to the tech writing team.
Arjun: We also need to review the Q4 budget proposal.
  Still no owner decided for this.
""".strip()


def _rand(prefix: str) -> str:
    return f"{prefix}-{random.randint(1000, 9999)}"


def jira_create_account(employee_id: str) -> dict:
    """Simulates JIRA provisioning. Fails on first call to demo retry logic."""
    global _jira_call_counts
    attempt = _jira_call_counts.get(employee_id, 0) + 1
    _jira_call_counts[employee_id] = attempt
    if attempt == 1:
        return {
            "status": "error",
            "code": 403,
            "message": "JIRA provisioning service temporarily unavailable. Please retry.",
            "retry_recommended": True,
            "attempt": attempt,
        }
    return {
        "status": "success",
        "user_id": _rand("JIRA"),
        "systems": ["JIRA Software", "Confluence"],
        "attempt": attempt,
    }


def gsuite_create_account(employee_id: str, role: str) -> dict:
    return {
        "status": "success",
        "email": f"{employee_id.lower()}@company.com",
        "role": role,
    }


def slack_create_account(employee_id: str, team: str) -> dict:
    return {
        "status": "success",
        "slack_handle": f"@{employee_id.lower()}",
        "team": team,
    }


def hr_get_employee(employee_id: str) -> dict:
    return {
        "status": "success",
        "employee_id": employee_id,
        "name": "Priya Sharma",
        "role": "Senior Software Engineer",
        "team": "Platform Engineering",
        "manager": "Arjun Mehta",
        "email": "priya.sharma@company.com",
        "timezone": "IST",
    }


def hr_assign_buddy(team: str) -> dict:
    return {
        "status": "assigned",
        "buddy": {"name": "Rahul Desai", "id": "EMP-442"},
        "team": team,
    }


def it_escalation_ticket(employee_id: str, error_details: str) -> dict:
    return {
        "status": "ticket_created",
        "ticket_id": _rand("IT"),
        "priority": "HIGH",
        "sla_hours": 4,
        "employee_id": employee_id,
        "error_details": error_details,
    }


def calendar_schedule_orientation(employee_id: str, manager: str) -> dict:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "status": "scheduled",
        "event_id": _rand("CAL"),
        "date": tomorrow,
        "time": "10:00 AM IST",
        "employee_id": employee_id,
        "manager": manager,
    }


def slack_send_welcome(name: str) -> dict:
    return {
        "status": "sent",
        "message": f"Welcome {name}! Here is your Day 1 checklist",
    }


def project_tracker_create_task(task: str, owner: str) -> dict:
    return {
        "status": "success",
        "task_id": _rand("TASK"),
        "task": task,
        "owner": owner,
    }


def send_clarification_request(task: str, reason: str) -> dict:
    return {
        "status": "sent",
        "flag_id": _rand("FLAG"),
        "sent_to": "meeting_host@company.com",
        "task": task,
        "reason": reason,
    }


def get_sla_status(approval_id: str) -> dict:
    return {
        "status": "BREACHED",
        "approval_id": approval_id,
        "hours_pending": 52,
        "sla_threshold_hours": 48,
        "assigned_approver": "Deepak Joshi",
        "approver_status": "ON_LEAVE",
        "leave_return_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    }


def get_delegation_registry(approver_name: str) -> dict:
    if approver_name == "Deepak Joshi":
        return {"delegate": "Kavya Reddy", "authority": "Full"}
    return {"delegate": "Department Head", "authority": "Limited"}


def reroute_approval(approval_id: str, delegate_name: str, reason: str) -> dict:
    return {
        "status": "rerouted",
        "approval_id": approval_id,
        "delegate_name": delegate_name,
        "reason": reason,
        "override_logged": True,
        "notification_sent": True,
    }


def check_it_ticket_sla(ticket_id: str) -> dict:
    return {
        "status": "OPEN",
        "ticket_id": ticket_id,
        "hours_open": 1,
        "sla_threshold_hours": 4,
        "at_risk": False,
        "assigned_to": "IT Helpdesk",
    }


def get_meeting_transcript() -> str:
    return SAMPLE_TRANSCRIPT


def reset_jira_mock() -> None:
    """Reset JIRA mock so the next run fails on the first attempt again."""
    global _jira_call_counts
    _jira_call_counts = {}
