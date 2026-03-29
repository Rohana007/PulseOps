"""Business impact calculators for PulseOps workflows."""

from __future__ import annotations


def calculate_onboarding_impact(
    steps_completed: int,
    steps_escalated: int,
    time_seconds: float,
) -> dict:
    manual_hours = 4.5
    hourly_rate = 1500
    monthly_hires = 30
    automated_minutes = time_seconds / 60
    manual_minutes = manual_hours * 60
    time_saved_minutes = manual_minutes - automated_minutes
    cost_saved_per_hire = (time_saved_minutes / 60) * hourly_rate
    monthly_savings = cost_saved_per_hire * monthly_hires
    return {
        "time_saved_minutes": round(time_saved_minutes, 1),
        "cost_saved_per_hire_inr": round(cost_saved_per_hire),
        "monthly_savings_inr": round(monthly_savings),
        "annual_savings_inr": round(monthly_savings * 12),
        "escalations_auto_handled": steps_escalated,
        "human_interventions_required": 0 if steps_escalated == 0 else 1,
        "steps_completed": steps_completed,
    }


def calculate_meeting_impact(tasks_created: int, flagged: int) -> dict:
    completion_lift = 0.40
    value_per_task = 2500
    additional_completions = round(tasks_created * completion_lift)
    value_unlocked = additional_completions * value_per_task
    return {
        "tasks_created": tasks_created,
        "items_flagged": flagged,
        "additional_completions_per_month": additional_completions * 4,
        "monthly_value_unlocked_inr": value_unlocked * 4,
        "ambiguity_errors_prevented": flagged,
    }


def calculate_sla_impact(breach_hours: int) -> dict:
    sla_penalty = 82000
    monthly_approvals = 200
    breach_rate_without = 0.08
    breach_rate_with = 0.005
    monthly_breaches_prevented = monthly_approvals * (breach_rate_without - breach_rate_with)
    monthly_savings = monthly_breaches_prevented * sla_penalty
    return {
        "breach_prevented": True,
        "penalty_avoided_inr": sla_penalty,
        "monthly_breaches_prevented": round(monthly_breaches_prevented, 1),
        "monthly_savings_inr": round(monthly_savings),
        "resolution_time_hours": breach_hours,
        "without_pulseops": "Manual discovery, days to resolve",
        "with_pulseops": "Auto-detected and rerouted in seconds",
    }


def calculate_total_impact() -> dict:
    return {
        "onboarding_annual_inr": 2268000,
        "meeting_annual_inr": 1200000,
        "sla_annual_inr": 984000,
        "total_annual_inr": 4452000,
        "pulseops_cost_inr": 60000,
        "roi_multiplier": 74,
        "payback_days": 5,
    }
