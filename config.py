"""PulseOps configuration and feature flags."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _configured(*keys: str) -> bool:
    """Return True only when all env vars are present and not placeholder values."""
    placeholders = {
        "",
        "your_free_key_from_aistudio_google_com",
        "https://hooks.slack.com/services/your/webhook/url",
        "xoxb-your-token",
        "https://yourcompany.atlassian.net",
        "your@email.com",
        "your_jira_token",
        "your_calendar_id@group.calendar.google.com",
        "your_spreadsheet_id",
        "path/to/service_account.json",
        "your_trello_key",
        "your_trello_token",
        "your_board_id",
    }
    for key in keys:
        value = (os.getenv(key) or "").strip()
        if value in placeholders:
            return False
    return True


def _file_exists_env(key: str) -> bool:
    value = (os.getenv(key) or "").strip()
    if not value or value == "path/to/service_account.json":
        return False
    return Path(value).exists()


USE_REAL_APIS = os.getenv("USE_REAL_APIS", "false").lower() == "true"

REAL_SLACK = USE_REAL_APIS and _configured("SLACK_WEBHOOK_URL")
REAL_JIRA = USE_REAL_APIS and _configured("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN")
REAL_CALENDAR = USE_REAL_APIS and _configured("GOOGLE_CALENDAR_ID", "GOOGLE_SERVICE_ACCOUNT_JSON") and _file_exists_env("GOOGLE_SERVICE_ACCOUNT_JSON")
REAL_SHEETS = USE_REAL_APIS and _configured("GOOGLE_SHEETS_ID", "GOOGLE_SERVICE_ACCOUNT_JSON") and _file_exists_env("GOOGLE_SERVICE_ACCOUNT_JSON")
REAL_TRELLO = USE_REAL_APIS and _configured("TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID")
