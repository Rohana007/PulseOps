"""
PulseOps — Custom Scenario Agent
Plans arbitrary enterprise workflows from plain English and simulates step-by-step execution with audit logging.
Uses Gemini via the shared PulseOps client.
"""

from __future__ import annotations

import json
import re
import time

from tools.audit_ledger import log_action
from utils.gemini_client import generate_text


def _parse_plan_json(text: str) -> list:
    text = re.sub(r"```(?:json)?|```", "", text, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
    return []


def run_custom_scenario(scenario_description: str, workflow_id: str):
    """
    Generator: plan scenario with Gemini, yield each executed step for live UI.
    """
    plan_prompt = f"""
You are PulseOps, an autonomous enterprise AI operations system.
A judge has given you this scenario to handle:

"{scenario_description}"

Break this into 4-6 autonomous agent steps. Be realistic and enterprise-appropriate.
Return ONLY a JSON array. No markdown. No explanation.

Each step must have:
- step: integer (1, 2, 3...)
- action: what the agent does (short, clear)
- agent: which agent handles it (OrchestratorAgent, ActionAgent, VerificationAgent, or AuditAgent)
- tool: what tool/system is called (e.g. "HR System", "JIRA API", "Email Service", "ERP", "Slack")
- result: realistic outcome of this step
- status: one of SUCCESS, FLAGGED, ESCALATED, RETRY
- reasoning: why the agent did this (1-2 sentences, professional tone)
- has_complication: true for exactly ONE step (to show error handling)
- complication: what goes wrong (only if has_complication=true)
- resolution: how the agent resolves it (only if has_complication=true)
"""

    raw = generate_text(plan_prompt, max_output_tokens=2048)
    steps = _parse_plan_json(raw)

    if not steps:
        yield {
            "step": 1,
            "action": "Failed to parse scenario",
            "status": "ERROR",
            "detail": "Could not generate workflow plan.",
            "agent": "OrchestratorAgent",
        }
        return

    total = len(steps)

    log_action(
        workflow=workflow_id,
        agent="OrchestratorAgent",
        step=0,
        action="Parse and plan custom scenario",
        tool_called="gemini (LLM)",
        result=f"Generated {total}-step workflow plan for: {scenario_description[:60]}...",
        status="SUCCESS",
        reasoning="Custom scenario received. Decomposed into autonomous agent steps using LLM planning.",
    )

    for s in steps:
        time.sleep(0.75)

        step_num = int(s.get("step", 0) or 0)
        action = s.get("action", "Execute step")
        agent = s.get("agent", "ActionAgent")
        tool = s.get("tool", "Internal System")
        result_txt = s.get("result", "Step completed")
        status = s.get("status", "SUCCESS")
        reasoning = s.get("reasoning", "Autonomous execution.")
        has_complication = bool(s.get("has_complication", False))
        complication = s.get("complication", "")
        resolution = s.get("resolution", "")

        if has_complication:
            time.sleep(0.4)
            log_action(
                workflow=workflow_id,
                agent=agent,
                step=step_num,
                action=f"{action} — COMPLICATION DETECTED",
                tool_called=str(tool),
                result=f"Issue: {complication}",
                status="RETRY",
                retry_count=1,
                reasoning=f"Unexpected issue: {complication}. Attempting resolution...",
            )
            yield {
                "step": step_num,
                "action": f"{action} — Issue Detected",
                "status": "RETRY",
                "detail": complication,
                "agent": agent,
                "is_complication": True,
            }
            time.sleep(0.6)

            log_action(
                workflow=workflow_id,
                agent=agent,
                step=step_num,
                action=f"{action} — Resolved",
                tool_called=str(tool),
                result=f"Resolution: {resolution}",
                status="SUCCESS",
                retry_count=1,
                reasoning=f"Complication resolved: {resolution}",
            )
            yield {
                "step": step_num,
                "action": f"{action} — Resolved ✓",
                "status": "SUCCESS",
                "detail": resolution,
                "agent": agent,
                "is_resolution": True,
            }
        else:
            log_action(
                workflow=workflow_id,
                agent=agent,
                step=step_num,
                action=action,
                tool_called=str(tool),
                result=result_txt,
                status=status,
                reasoning=reasoning,
            )
            yield {
                "step": step_num,
                "action": action,
                "status": status,
                "detail": result_txt,
                "agent": agent,
            }

    time.sleep(0.4)
    log_action(
        workflow=workflow_id,
        agent="AuditAgent",
        step=total + 1,
        action="Generate workflow completion report",
        tool_called="audit_report",
        result=f"All {total} steps completed. Audit trail logged.",
        status="SUCCESS",
        reasoning="Workflow complete. Compliance report generated and stored in audit ledger.",
    )
    yield {
        "step": total + 1,
        "action": "Workflow Complete — Audit Report Generated",
        "status": "SUCCESS",
        "detail": f"All {total} steps executed autonomously",
        "agent": "AuditAgent",
        "is_final": True,
    }
