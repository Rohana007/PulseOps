# PulseOps Demo Checklist

## Before You Start

- Ensure `.env` is present and `GEMINI_API_KEY` is valid.
- Confirm Streamlit starts with `streamlit run main.py`.
- Confirm the integration bar shows the expected state:
  - Slack: `LIVE`
  - JIRA: `LIVE` or `MOCK`
  - Calendar: `LIVE`
  - Trello: `MOCK` unless configured
- Click `Reset` before the demo so JIRA retry behavior resets.
- Keep Slack and Google Calendar open in separate tabs if you want to show real delivery.

## Submission Assets

- Working prototype: ready in Streamlit
- Architecture document: `ARCHITECTURE_AND_IMPACT.md`
- Project overview: `README.md`
- Pitch video: follow the sequence below

## Demo Flow

### 1. Show Readiness

- Open the PulseOps dashboard.
- Point out the integration status bar.
- Mention that the UI shows observed metrics, while the README and architecture doc contain the estimated impact model with explicit assumptions.

### 2. Run Onboarding

Use:

```text
Onboard new employee EMP-2026-001 starting Monday
```

Verify:

- Orchestrator plan appears
- OnboardAgent runs
- JIRA retry logic is visible
- orientation scheduling appears
- welcome message appears
- audit ledger fills in
- thought chain fills in

If live integrations are available, verify:

- Slack welcome message delivered
- calendar event created
- JIRA action recorded as live or mock according to configuration

### 3. Run Meeting Workflow

Use:

```text
Process Platform Engineering Sync meeting transcript
```

Verify:

- tasks are created for clear owners
- ambiguous items are flagged, not guessed
- Slack meeting summary includes actual task and flagged-item details
- audit ledger shows flagged actions clearly

### 4. Run SLA Workflow

Use:

```text
SLA breach on PROC-4821 requires immediate rerouting
```

Verify:

- SLAAgent runs
- delegate lookup is visible
- reroute action is logged
- explanation panel works for one compliance step

## Explainability Check

- Open `Why Did You Do That?`
- Choose one audit step
- Click `Explain`
- Confirm you receive a clear plain-English explanation

## What To Mention Verbally

- PulseOps is multi-agent, not just a chatbot with tools.
- The orchestrator delegates to specialists and can trigger handoffs.
- The system is resilient: failures are retried, escalated, or rerouted instead of breaking the workflow.
- Every important action is logged with reasoning and status.
- The live UI shows factual run data; the impact model is documented separately with assumptions.

## Backup Plan

If a live API fails during the demo:

- point to the fallback-safe architecture
- show that the workflow still completes
- show `api_source` in the audit ledger
- explain that PulseOps degrades gracefully instead of crashing

## Final 20-Second Close

- PulseOps automates fragmented enterprise operations end to end.
- It handles onboarding, meeting follow-through, and SLA recovery with auditability and exception handling.
- It is built to be affordable, explainable, and practical for mid-market teams.
