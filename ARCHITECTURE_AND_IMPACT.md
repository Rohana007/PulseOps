# PulseOps Architecture And Impact

## Overview

PulseOps is an autonomous multi-agent enterprise operations system built for ET AI Hackathon 2026.
It is designed to handle common operational breakdowns across onboarding, meeting follow-through, and SLA recovery with auditability, fallback behavior, and human-readable explanations.

## Problem Areas

- Onboarding delays create poor first-week experiences and force HR and IT into manual follow-up.
- Meeting action items are often lost because ownership is unclear or never converted into tracked work.
- Approval workflows breach SLA when the approver is unavailable and nobody notices in time.

## System Architecture

```text
User Event
   |
   v
Orchestrator
   |- OnboardAgent
   |- MeetingAgent
   |- SLAAgent
   `- TicketMonitorAgent (handoff when escalation occurs)
         |
         v
API Router -> Real API / Mock API / Mock Fallback
         |
         v
Audit Ledger -> Explainer -> Streamlit Dashboard
```

## Agent Roles

### Orchestrator

- receives the enterprise event
- selects which specialist agents to activate
- executes them in sequence
- monitors outcomes
- triggers handoffs automatically when escalation conditions are met

### OnboardAgent

- fetches employee profile
- provisions GSuite, Slack, and JIRA access
- retries JIRA once on failure
- escalates to IT if needed
- assigns onboarding buddy
- schedules orientation
- sends welcome message

### MeetingAgent

- parses a meeting transcript into action items
- creates tasks for clearly owned items
- flags ambiguous items instead of guessing
- sends a meeting summary to attendees

### SLAAgent

- checks approval or ticket SLA state
- identifies blocked approvers
- looks up delegates
- reroutes the approval when policy allows

## Tool Integrations

PulseOps supports both live and simulated execution.

### Live Integrations

- Slack webhook
- Google Calendar
- Google Sheets
- JIRA REST API
- Trello API

### Fallback Strategy

- every live API call is wrapped in error handling
- if the real integration fails, PulseOps falls back to a mock where supported
- the audit log records whether the result came from `REAL_API`, `MOCK`, or `MOCK_FALLBACK`

## Error Handling Logic

PulseOps is designed to recover instead of stopping.

- onboarding never stops at JIRA failure
- JIRA provisioning is retried once before escalation
- meeting ambiguity is flagged rather than guessed
- SLA rerouting is logged for compliance
- orchestrator can trigger a follow-up monitoring agent after escalation

## Auditability

Every meaningful action writes to SQLite with:

- workflow ID
- agent name
- thought
- action
- tool called
- result
- status
- confidence
- API source

The dashboard exposes these records in the live audit ledger and supports a "Why did you do that?" explanation flow for non-technical reviewers.

## Communication Model

PulseOps agents communicate through the orchestrator and shared workflow state.

- the Orchestrator delegates to specialists
- specialists return structured results and thought chains
- the Orchestrator evaluates those results
- if escalation conditions are detected, it activates downstream agents automatically

This creates visible multi-agent coordination rather than a single chatbot with tool calls.

## Estimated Impact Model

These are benchmark-based estimates for judging and business modeling, not measured accounting outcomes from a production deployment.

### Onboarding

Assumptions:

- manual onboarding effort: `4.5 hours` per hire
- blended operations cost: `INR 1,500/hour`
- monthly hiring volume: `30 hires/month`

Estimate:

- `4.5 x 1,500 = INR 6,750` estimated manual effort cost per hire
- `INR 6,750 x 30 = INR 202,500/month`
- `INR 202,500 x 12 = INR 2,430,000/year`

### Meeting Follow-Through

Assumptions:

- `40%` of action items are lost or delayed without structured follow-through
- `INR 2,500` conservative value per recovered task
- `4 meetings/month` with at least `4 clear action items` each

Estimate:

- `4 x 40% = 1.6` additional tasks recovered per meeting
- `1.6 x INR 2,500 = INR 4,000` value per meeting
- `INR 4,000 x 4 = INR 16,000/month`
- `INR 16,000 x 12 = INR 192,000/year`

### SLA Recovery

Assumptions:

- avoided cost per material breach: `INR 82,000`
- `200 approvals/month`
- breach rate without automation: `8%`
- breach rate with automation: `0.5%`

Estimate:

- `200 x (8% - 0.5%) = 15` breaches prevented per month
- `15 x INR 82,000 = INR 1,230,000/month`
- `INR 1,230,000 x 12 = INR 14,760,000/year`

## Demo Notes

In the live demo, use observed metrics from the dashboard:

- workflow duration
- successful actions
- escalations
- flagged ambiguities
- live versus mock API calls
- notifications sent

In the architecture document and pitch, use the impact model above with the assumptions stated clearly.

## Why This Matters

PulseOps gives mid-market teams a lower-cost alternative to enterprise workflow suites by combining:

- autonomous orchestration
- exception handling
- auditability
- explainability
- practical integrations with tools teams already use

That makes it suitable both as a hackathon prototype and as the basis for a real operations product.
