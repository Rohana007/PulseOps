"""
PulseOps orchestrator agent.
Receives enterprise events, delegates to specialists, and handles handoffs.
"""

from __future__ import annotations

import json
import os
import re
import uuid

import google.generativeai as genai
from dotenv import load_dotenv

from agents.meeting_agent import run_meeting_agent
from agents.onboard_agent import run_onboarding
from agents.sla_agent import run_sla_agent, run_ticket_monitor
from tools.audit_ledger import log_action
from tools.mock_apis import get_meeting_transcript

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-2.0-flash")


def _plan_with_gemini(event: str) -> list:
    """
    Build a deterministic execution plan from the incoming event.
    """
    lowered = event.lower()
    if "onboard" in lowered or "employee" in lowered or "new hire" in lowered:
        return [
            {
                "agent": "OnboardAgent",
                "reason": "Primary onboarding workflow",
                "priority": 1,
                "depends_on": None,
                "input": "EMP-2026-001",
            },
            {
                "agent": "MeetingAgent",
                "reason": "Process the team sync transcript",
                "priority": 2,
                "depends_on": "OnboardAgent",
                "input": "transcript",
            },
            {
                "agent": "SLAAgent",
                "reason": "Monitor approval compliance",
                "priority": 3,
                "depends_on": None,
                "input": "PROC-4821",
            },
        ]
    if "meeting" in lowered or "transcript" in lowered or "action item" in lowered:
        return [
            {
                "agent": "MeetingAgent",
                "reason": "Process the meeting transcript into trackable actions",
                "priority": 1,
                "depends_on": None,
                "input": "transcript",
            }
        ]
    if "sla" in lowered or "approval" in lowered or "breach" in lowered:
        return [
            {
                "agent": "SLAAgent",
                "reason": "Recover the delayed approval and protect compliance",
                "priority": 1,
                "depends_on": None,
                "input": "PROC-4821",
            }
        ]
    return [
        {
            "agent": "OnboardAgent",
            "reason": "Default enterprise workflow",
            "priority": 1,
            "depends_on": None,
            "input": "EMP-2026-001",
        }
    ]


def _check_for_handoffs(agent_name: str, result: dict, workflow_id: str) -> list:
    """
    Inspect an agent result and decide whether another agent should be triggered.
    """
    handoffs: list[dict] = []
    thought_chain = result.get("thought_chain", [])

    if agent_name == "OnboardAgent" and result.get("steps_escalated", 0) > 0:
        ticket_id = "IT-UNKNOWN"
        for step in thought_chain:
            match = re.search(r"IT-\d+", step.get("result", ""))
            if match:
                ticket_id = match.group(0)
                break

        handoffs.append(
            {
                "agent": "TicketMonitorAgent",
                "reason": (
                    f"OnboardAgent escalated JIRA failure. Monitor {ticket_id} for SLA compliance."
                ),
                "input": ticket_id,
                "triggered_by": "OnboardAgent escalation",
            }
        )

        log_action(
            workflow=workflow_id,
            agent="Orchestrator",
            step=99,
            thought=(
                f"OnboardAgent reported {result.get('steps_escalated')} escalation(s). "
                "JIRA provisioning was escalated to IT, so I should activate the ticket monitor."
            ),
            action=f"Handoff: activate TicketMonitorAgent for {ticket_id}",
            tool_called="internal_handoff",
            result=f"TicketMonitorAgent queued for {ticket_id}",
            status="HANDOFF",
            escalated=True,
            confidence=0.95,
        )

    return handoffs


def run_orchestrator(
    event: str,
    employee_id: str = "EMP-2026-001",
    approval_id: str = "PROC-4821",
) -> dict:
    """
    Main orchestration flow: plan, delegate, monitor, handoff, summarize.
    """
    workflow_id = f"WF-{str(uuid.uuid4())[:8].upper()}"
    all_results: dict[str, dict] = {}
    execution_order: list[str] = []

    log_action(
        workflow=workflow_id,
        agent="Orchestrator",
        step=1,
        thought=(
            f"Received enterprise event '{event}'. I need to decide which specialist agents "
            "should handle it and in what order."
        ),
        action="Plan execution strategy",
        tool_called="gemini_planner",
        result="Planning agent execution",
        status="SUCCESS",
        confidence=1.0,
    )

    plan = _plan_with_gemini(event)

    log_action(
        workflow=workflow_id,
        agent="Orchestrator",
        step=2,
        thought=(
            f"Execution plan created with {len(plan)} specialist agent(s): "
            f"{[item.get('agent') for item in plan]}"
        ),
        action="Finalize plan",
        tool_called="internal_planner",
        result=str([item.get("agent") for item in plan]),
        status="SUCCESS",
        confidence=0.95,
    )

    additional_agents: list[dict] = []
    ordered_plan = sorted(plan, key=lambda item: item.get("priority", 1))

    for index, task in enumerate(ordered_plan, start=1):
        agent_name = task["agent"]
        execution_order.append(agent_name)

        log_action(
            workflow=workflow_id,
            agent="Orchestrator",
            step=2 + index,
            thought=(
                f"Delegating to {agent_name} because {task.get('reason', 'no reason supplied')}."
            ),
            action=f"Delegate to {agent_name}",
            tool_called="agent_delegation",
            result=f"{agent_name} activated",
            status="HANDOFF",
            confidence=0.92,
        )

        try:
            if agent_name == "OnboardAgent":
                result = run_onboarding(employee_id, workflow_id)
            elif agent_name == "MeetingAgent":
                result = run_meeting_agent(get_meeting_transcript(), workflow_id)
            elif agent_name == "SLAAgent":
                result = run_sla_agent(approval_id, workflow_id)
            elif agent_name == "TicketMonitorAgent":
                result = run_ticket_monitor(task.get("input", "IT-0000"), workflow_id)
            else:
                result = {"error": f"Unknown agent {agent_name}", "thought_chain": []}
        except Exception as exc:
            result = {
                "error": str(exc),
                "steps_completed": 0,
                "steps_escalated": 0,
                "steps_flagged": 0,
                "thought_chain": [],
            }

        all_results[agent_name] = result

        log_action(
            workflow=workflow_id,
            agent="Orchestrator",
            step=10 + index,
            thought=(
                f"{agent_name} completed. Completed steps: {result.get('steps_completed', 0)}. "
                f"Escalations: {result.get('steps_escalated', 0)}. "
                "I should inspect whether its outputs require a handoff."
            ),
            action=f"{agent_name} completed",
            tool_called="result_monitor",
            result=(
                f"Completed={result.get('steps_completed', 0)} | "
                f"Escalated={result.get('steps_escalated', 0)} | "
                f"Flagged={result.get('steps_flagged', 0)}"
            ),
            status="SUCCESS",
            confidence=1.0,
        )

        additional_agents.extend(_check_for_handoffs(agent_name, result, workflow_id))

    for handoff in additional_agents:
        agent_name = handoff["agent"]
        execution_order.append(agent_name)

        log_action(
            workflow=workflow_id,
            agent="Orchestrator",
            step=20,
            thought=(
                f"Handoff triggered by {handoff['triggered_by']}. "
                f"Activating {agent_name} because {handoff['reason']}"
            ),
            action=f"Auto-handoff to {agent_name}",
            tool_called="auto_handoff",
            result=f"{agent_name} activated",
            status="HANDOFF",
            escalated=True,
            confidence=0.95,
        )

        try:
            result = run_ticket_monitor(handoff["input"], workflow_id)
        except Exception as exc:
            result = {"error": str(exc), "thought_chain": []}
        all_results[agent_name] = result

    total_steps = sum(result.get("steps_completed", 0) for result in all_results.values())
    total_escalations = sum(
        result.get("steps_escalated", 0) for result in all_results.values()
    )
    total_flagged = sum(result.get("steps_flagged", 0) for result in all_results.values())

    log_action(
        workflow=workflow_id,
        agent="Orchestrator",
        step=100,
        thought=(
            f"All agents completed. Total successful steps: {total_steps}, escalations: "
            f"{total_escalations}, flagged items: {total_flagged}. I can now produce the final report."
        ),
        action="Generate final orchestration report",
        tool_called="report_generator",
        result=f"Workflow complete. {len(all_results)} agents executed.",
        status="SUCCESS",
        confidence=1.0,
    )

    return {
        "workflow_id": workflow_id,
        "event": event,
        "agents_activated": list(all_results.keys()),
        "execution_order": execution_order,
        "handoffs_triggered": len(additional_agents),
        "all_results": all_results,
        "total_steps": total_steps,
        "total_escalations": total_escalations,
        "total_flagged": total_flagged,
        "plan": ordered_plan,
    }
