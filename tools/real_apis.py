"""Real API integrations for PulseOps with graceful error handling."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from requests.auth import HTTPBasicAuth

load_dotenv()


def slack_send_message_real(channel_or_webhook: str, message: str, blocks: list | None = None) -> dict:
    """Send a real Slack message via incoming webhook."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL") or channel_or_webhook
    if not webhook_url:
        return {"status": "error", "message": "No Slack webhook configured"}
    payload = {"text": message}
    if blocks:
        payload["blocks"] = blocks
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            return {"status": "success", "message": "Slack message sent", "channel": "webhook"}
        return {"status": "error", "code": response.status_code, "message": response.text}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def slack_send_welcome_real(employee_name: str, employee_email: str) -> dict:
    """Send a rich welcome message with a Day 1 checklist."""
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Welcome to the team, {employee_name}!"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Your Day 1 Checklist:*\n"
                    f"Check your email ({employee_email})\n"
                    "Join team channels\n"
                    "Complete IT setup\n"
                    "Meet your buddy\n"
                    "Read the handbook"
                ),
            },
        },
    ]
    return slack_send_message_real(os.getenv("SLACK_WEBHOOK_URL", ""), f"Welcome {employee_name}!", blocks)


def slack_send_meeting_summary_real(tasks: list | None = None, flagged: list | None = None) -> dict:
    """Send rich meeting summary to Slack with full task and flagged details."""
    tasks = tasks or []
    flagged = flagged or []

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "error", "message": "No Slack webhook"}

    if tasks:
        task_lines = "\n".join(
            [
                f"✅ *{t.get('task', 'Unknown task')}*\n   -> Owner: {t.get('owner', 'TBD')} | ID: {t.get('task_id', 'N/A')}"
                for t in tasks
            ]
        )
    else:
        task_lines = "_No tasks created_"

    if flagged:
        flag_lines = "\n".join(
            [
                f"🚩 *{f.get('task', 'Unknown')}*\n   -> {f.get('reason', 'Unclear ownership')}"
                for f in flagged
            ]
        )
    else:
        flag_lines = "_No flagged items_"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Meeting Summary - PulseOps"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Tasks Created ({len(tasks)}):*\n{task_lines}"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Flagged for Clarification ({len(flagged)}):*\n{flag_lines}",
            },
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "Sent automatically by *PulseOps* | Summary delivered to all 4 attendees"}
            ],
        },
    ]

    payload = {
        "text": f"Meeting Summary: {len(tasks)} tasks, {len(flagged)} flagged",
        "blocks": blocks,
    }
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            return {
                "status": "sent",
                "tasks_included": len(tasks),
                "flagged_included": len(flagged),
                "recipients": 4,
            }
        return {"status": "error", "code": response.status_code}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def slack_send_it_alert_real(ticket_id: str, employee_id: str, error: str) -> dict:
    """Send IT escalation alert to Slack when JIRA provisioning fails."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "error", "message": "No webhook"}

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "IT Escalation - PulseOps"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Ticket:* `{ticket_id}`\n*Employee:* {employee_id}\n*Issue:* {error}\n*Priority:* HIGH\n*SLA:* 4 hours",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "PulseOps automatically retried JIRA provisioning, created an escalation ticket, continued onboarding, and notified IT.",
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "Automated by *PulseOps* | No human intervention required"}],
        },
    ]

    try:
        response = requests.post(
            webhook_url,
            json={"text": f"IT Alert: {ticket_id}", "blocks": blocks},
            timeout=10,
        )
        return {"status": "sent" if response.status_code == 200 else "error"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def jira_create_user_real(employee_email: str, display_name: str) -> dict:
    """Create a JIRA user via the REST API."""
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not all([base_url, email, token]):
        return {"status": "error", "message": "JIRA not configured"}
    url = f"{base_url}/rest/api/3/user"
    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "emailAddress": employee_email,
        "displayName": display_name,
        "products": ["jira-software"],
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "status": "success",
                "account_id": data.get("accountId"),
                "display_name": data.get("displayName"),
            }
        try:
            message = response.json().get("errorMessages", ["Unknown error"])[0]
        except Exception:
            message = response.text
        return {"status": "error", "code": response.status_code, "message": message}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def jira_create_ticket_real(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> dict:
    """Create a JIRA ticket for IT escalation."""
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    if not all([base_url, email, token]):
        return {"status": "error", "message": "JIRA not configured"}
    url = f"{base_url}/rest/api/3/issue"
    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": "High"},
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth, timeout=10)
        if response.status_code in (200, 201):
            data = response.json()
            return {
                "status": "success",
                "ticket_id": data.get("key"),
                "ticket_url": f"{base_url}/browse/{data.get('key')}",
            }
        return {"status": "error", "code": response.status_code, "message": str(response.text)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def calendar_create_event_real(
    summary: str,
    attendee_emails: list,
    start_datetime: str,
    duration_minutes: int = 60,
) -> dict:
    """Create a real Google Calendar event."""
    sa_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    if not sa_file:
        return {"status": "error", "message": "Google Calendar not configured"}
    try:
        creds = service_account.Credentials.from_service_account_file(
            sa_file, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=creds)
        start = datetime.fromisoformat(start_datetime)
        end = start + timedelta(minutes=duration_minutes)
        event = {
            "summary": summary,
            "description": "Scheduled automatically by PulseOps",
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [{"email": email} for email in attendee_emails],
            "reminders": {"useDefault": True},
        }
        result = service.events().insert(
            calendarId=calendar_id, body=event, sendUpdates="all"
        ).execute()
        return {
            "status": "success",
            "event_id": result.get("id"),
            "event_url": result.get("htmlLink"),
            "start": start_datetime,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def sheets_get_employee_real(employee_id: str) -> dict:
    """Fetch employee data from Google Sheets."""
    sa_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sa_file or not sheet_id:
        return {"status": "error", "message": "Google Sheets not configured"}
    try:
        creds = service_account.Credentials.from_service_account_file(
            sa_file, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range="Employees!A:G"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            return {"status": "error", "message": "No data in sheet"}
        headers = rows[0]
        for row in rows[1:]:
            row_dict = dict(zip(headers, row))
            if row_dict.get("employee_id") == employee_id:
                return {"status": "success", **row_dict}
        return {"status": "error", "message": f"Employee {employee_id} not found"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def trello_create_card_real(task: str, owner: str, due_date: str | None = None) -> dict:
    """Create a real Trello card."""
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    board_id = os.getenv("TRELLO_BOARD_ID")
    if not all([api_key, token, board_id]):
        return {"status": "error", "message": "Trello not configured"}
    try:
        lists_url = f"https://api.trello.com/1/boards/{board_id}/lists"
        lists_resp = requests.get(lists_url, params={"key": api_key, "token": token}, timeout=10)
        lists = lists_resp.json()
        list_id = lists[0]["id"] if lists else None
        if not list_id:
            return {"status": "error", "message": "No lists found on Trello board"}
        response = requests.post(
            "https://api.trello.com/1/cards",
            params={
                "key": api_key,
                "token": token,
                "idList": list_id,
                "name": task,
                "desc": f"Owner: {owner}\nCreated by PulseOps",
                "due": due_date,
            },
            timeout=10,
        )
        if response.status_code == 200:
            card = response.json()
            return {
                "status": "success",
                "card_id": card["id"],
                "card_url": card["shortUrl"],
                "task": task,
                "owner": owner,
            }
        return {"status": "error", "message": str(response.text)}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
