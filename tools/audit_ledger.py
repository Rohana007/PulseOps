"""SQLite-backed append-only audit ledger for PulseOps."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.getenv("PULSEOPS_DB_PATH", "")).expanduser() if os.getenv("PULSEOPS_DB_PATH") else Path(__file__).resolve().parent.parent / "pulseops_audit.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    """Create the audit table if it does not already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                workflow TEXT,
                agent TEXT,
                step INTEGER,
                thought TEXT,
                action TEXT,
                tool_called TEXT,
                result TEXT,
                status TEXT,
                retry_count INTEGER DEFAULT 0,
                escalated BOOLEAN DEFAULT FALSE,
                confidence REAL DEFAULT 1.0,
                api_source TEXT DEFAULT 'UNKNOWN'
            )
            """
        )
        columns = [row[1] for row in conn.execute("PRAGMA table_info(audit_log)").fetchall()]
        required_columns = {
            "thought": "ALTER TABLE audit_log ADD COLUMN thought TEXT",
            "confidence": "ALTER TABLE audit_log ADD COLUMN confidence REAL DEFAULT 1.0",
            "api_source": "ALTER TABLE audit_log ADD COLUMN api_source TEXT DEFAULT 'UNKNOWN'",
        }
        for column_name, ddl in required_columns.items():
            if column_name not in columns:
                conn.execute(ddl)
        conn.commit()


def log_action(
    workflow: str,
    agent: str,
    step: int,
    thought: str,
    action: str,
    result: str,
    status: str,
    tool_called: str | None = None,
    retry_count: int = 0,
    escalated: bool = False,
    confidence: float = 1.0,
    api_source: str = "UNKNOWN",
) -> None:
    """Insert a single audit log row."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO audit_log (
                timestamp, workflow, agent, step, thought, action, tool_called,
                result, status, retry_count, escalated, confidence, api_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                workflow,
                agent,
                step,
                thought,
                action,
                tool_called,
                result,
                status,
                retry_count,
                int(escalated),
                confidence,
                api_source,
            ),
        )
        conn.commit()


def get_audit_log(workflow: str | None = None) -> list[dict]:
    """Return audit rows ordered oldest to newest."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if workflow:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE workflow = ? ORDER BY id ASC",
                (workflow,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM audit_log ORDER BY id ASC").fetchall()
    return [dict(row) for row in rows]


def clear_log() -> None:
    """Delete all audit rows."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM audit_log")
        conn.commit()
