"""
PulseOps explainer engine.
Generates a plain-English answer for "Why did you do that?"
"""

from __future__ import annotations

import os

import google.generativeai as genai
from dotenv import load_dotenv

from tools.audit_ledger import get_audit_log

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-2.0-flash")


def _fallback_explanation(target: dict) -> str:
    thought = str(target.get("thought") or "the current workflow state")
    action = str(target.get("action") or "take the next workflow step")
    tool_called = str(target.get("tool_called") or "the relevant system")
    status = str(target.get("status") or "SUCCESS")
    result = str(target.get("result") or "No result recorded")
    sentence_1 = (
        f"This decision was triggered by {thought.lower().rstrip('.')}, which gave the agent enough context to act."
    )
    sentence_2 = (
        f"It chose to {action.lower().rstrip('.')} using {tool_called}, and the recorded result was {result[:120].rstrip('.') }."
    )
    sentence_3 = (
        f"That was the correct step because the workflow status was {status.lower()} and PulseOps is designed to keep work moving while preserving an audit trail."
    )
    return " ".join([sentence_1, sentence_2, sentence_3])


def explain_decision(workflow_id: str, step: int, agent: str | None = None) -> str:
    logs = get_audit_log(workflow_id)

    if agent:
        target = next(
            (entry for entry in logs if entry["step"] == step and entry["agent"] == agent),
            None,
        )
    else:
        target = next((entry for entry in logs if entry["step"] == step), None)

    if not target:
        return "No audit record found for this step."

    prompt = f"""
You are PulseOps. A non-technical operations manager clicked "Why did you do that?"

Explain in exactly 3 sentences:
1. What data or situation triggered this decision
2. What you chose to do and which system you called
3. Why this was the correct action per enterprise policy

Keep it clear and professional. No technical jargon.

Decision:
Agent: {target['agent']}
Thought: {target.get('thought', 'Not recorded')}
Action: {target['action']}
Tool: {target.get('tool_called', 'None')}
Result: {target['result']}
Status: {target['status']}
Escalated: {target['escalated']}
"""
    try:
        response = _model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else _fallback_explanation(target)
    except Exception:
        return _fallback_explanation(target)
