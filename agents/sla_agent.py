"""PulseOps SLA specialist agent."""

from __future__ import annotations

from tools import mock_apis
from tools.audit_ledger import log_action


def _with_source(payload: dict) -> dict:
    payload["_source"] = "MOCK"
    return payload


def _log_step(workflow_id: str, step: int, thought: str, action: str, tool_called: str, result: dict, status: str) -> dict:
    log_action(
        workflow=workflow_id,
        agent="SLAAgent",
        step=step,
        thought=thought,
        action=action,
        tool_called=tool_called,
        result=str(result)[:400],
        status=status,
        escalated=status == "ESCALATED",
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
    }


def run_sla_agent(approval_id: str, workflow_id: str) -> dict:
    thought_chain: list[dict] = []
    sla_status = _with_source(mock_apis.get_sla_status(approval_id))
    thought_chain.append(
        _log_step(
            workflow_id,
            1,
            "I need to inspect the approval first to confirm whether the SLA has actually been breached.",
            "Check approval SLA",
            "check_sla_status",
            sla_status,
            "SUCCESS",
        )
    )
    delegate = _with_source(mock_apis.get_delegation_registry(sla_status["assigned_approver"]))
    thought_chain.append(
        _log_step(
            workflow_id,
            2,
            "The assigned approver is unavailable, so I should look up the authorized delegate before rerouting.",
            "Lookup delegate",
            "lookup_delegate",
            delegate,
            "SUCCESS",
        )
    )
    reroute = _with_source(
        mock_apis.reroute_approval(
            approval_id,
            delegate["delegate"],
            "Original approver is on leave and the SLA threshold has been exceeded.",
        )
    )
    thought_chain.append(
        _log_step(
            workflow_id,
            3,
            "The approval is breached and a delegate exists, so rerouting is the compliant next step.",
            "Reroute approval",
            "reroute_to_delegate",
            reroute,
            "ESCALATED",
        )
    )
    return {
        "thought_chain": thought_chain,
        "steps_completed": len([t for t in thought_chain if t["status"] == "SUCCESS"]),
        "steps_escalated": len([t for t in thought_chain if t["status"] == "ESCALATED"]),
        "steps_flagged": 0,
        "steps_errored": 0,
        "total_steps": len(thought_chain),
        "final_message": "SLA breach handled and rerouted according to delegation policy.",
    }


def run_ticket_monitor(ticket_id: str, workflow_id: str) -> dict:
    ticket = _with_source(mock_apis.check_it_ticket_sla(ticket_id))
    thought_chain = [
        _log_step(
            workflow_id,
            1,
            "The IT escalation ticket was created earlier, so I should verify whether it is still within SLA.",
            "Check IT ticket SLA",
            "check_it_ticket_sla",
            ticket,
            "SUCCESS",
        )
    ]
    return {
        "thought_chain": thought_chain,
        "steps_completed": 1,
        "steps_escalated": 0,
        "steps_flagged": 0,
        "steps_errored": 0,
        "total_steps": 1,
        "final_message": "Ticket monitoring completed; the IT ticket is open but not yet at risk.",
    }
