# PulseOps

Autonomous multi-agent enterprise operations for onboarding, meeting follow-through, SLA recovery, and audit-first exception handling.

Built for the ET AI Hackathon 2026, PulseOps combines orchestrated specialist agents, real-or-mock integrations, and explainable execution in a demo-friendly Streamlit control room.

## Quick Links

- architecture and impact doc: [`ARCHITECTURE_AND_IMPACT.md`](ARCHITECTURE_AND_IMPACT.md)
- demo runbook: [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md)
- pitch script: [`PITCH_SCRIPT.md`](PITCH_SCRIPT.md)
- app entrypoint: [`main.py`](main.py)

## At A Glance

- multi-agent orchestration with specialist agents
- hybrid planning: Gemini first, deterministic fallback
- real and mock integrations with graceful degradation
- full audit trail with thought, action, status, confidence, and source
- plain-English explainability for non-technical reviewers
- Docker and local run support

## Quick Start

### Local

```bash
pip install -r requirements.txt
streamlit run main.py
```

### Docker

```bash
docker compose up --build
```

Open:

```text
http://localhost:8501
```

## Why PulseOps

PulseOps is designed to solve three common enterprise workflow failures:

- new-hire onboarding gets delayed across HR, IT, Slack, JIRA, and calendar systems
- meeting action items disappear because ownership is unclear or never tracked
- approvals breach SLA because the assigned approver is unavailable

Instead of using brittle rules, PulseOps uses an orchestrator and specialist agents that reason before acting, recover from failures, hand off work automatically, and explain every decision.

## What Makes It Different

- ReAct architecture: specialist execution supports reasoning traces before actions
- real multi-agent orchestration: the Orchestrator delegates to specialists and triggers handoffs
- hybrid planning: Gemini planning is supported, with deterministic fallback for demo reliability
- exception handling: JIRA failures trigger retry, escalation, and monitoring
- audit-first design: every meaningful action is written to SQLite with thought, result, and source
- real or mock integrations: Slack, JIRA, Google Calendar, Google Sheets, and Trello can run live or fall back safely
- ambiguity-safe behavior: the MeetingAgent never guesses unclear ownership

## Architecture

```text
User Event
   |
   v
Orchestrator
   |- OnboardAgent
   |- MeetingAgent
   |- SLAAgent
   `- TicketMonitorAgent (auto-triggered handoff)
         |
         v
API Router -> Real API / Mock API / Mock Fallback
         |
         v
Audit Ledger -> Explainer -> Streamlit Dashboard
```

## Project Structure

```text
pulseops/
|-- README.md
|-- ARCHITECTURE_AND_IMPACT.md
|-- DEMO_CHECKLIST.md
|-- PITCH_SCRIPT.md
|-- .env.example
|-- config.py
|-- main.py
|-- requirements.txt
|-- agents/
|   |-- orchestrator.py
|   |-- react_engine.py
|   |-- onboard_agent.py
|   |-- meeting_agent.py
|   `-- sla_agent.py
|-- tools/
|   |-- api_router.py
|   |-- audit_ledger.py
|   |-- mock_apis.py
|   `-- real_apis.py
`-- utils/
    |-- explainer.py
    `-- impact_calculator.py
```

## Core Components

### Orchestrator

[`agents/orchestrator.py`](agents/orchestrator.py) is the supervisor.
It interprets the enterprise event, plans agent activation, delegates to specialists, monitors outcomes, and triggers downstream handoffs when needed.

The current build keeps both modes:

- Gemini-based planning when the model is available
- deterministic fallback planning for demo reliability

### Specialist Agents

- [`agents/onboard_agent.py`](agents/onboard_agent.py): provisions employee workflows across HR, Slack, JIRA, orientation scheduling, and welcome messaging
- [`agents/meeting_agent.py`](agents/meeting_agent.py): parses transcript action items, creates tasks, and flags ambiguous ownership
- [`agents/sla_agent.py`](agents/sla_agent.py): handles approval rerouting and ticket SLA monitoring

### ReAct Engine

[`agents/react_engine.py`](agents/react_engine.py) contains the shared LangGraph ReAct runtime.
The current demo keeps this capability in the codebase while specialist workflows use deterministic execution for stability.

### Routing Layer

[`tools/api_router.py`](tools/api_router.py) decides whether to use:

- real APIs
- mock APIs
- mock fallback after a real API error

This keeps the app demo-safe while still supporting real integration value.

### Audit and Explainability

- [`tools/audit_ledger.py`](tools/audit_ledger.py): append-only SQLite audit trail
- [`utils/explainer.py`](utils/explainer.py): plain-English answer to "Why did you do that?"

### Business Value Layer

[`utils/impact_calculator.py`](utils/impact_calculator.py) contains the benchmark-based business model used for submission materials and pitch math.
The live dashboard now prioritizes observed run metrics so the product UI stays factual during demos.

## UI Features

The Streamlit dashboard in [`main.py`](main.py) includes:

- premium dark control-room UI
- API connection status bar
- orchestration plan display
- agent execution timeline
- full thought chain view
- live audit ledger
- live, mock, and fallback badges
- observed workflow metrics
- notification log
- explainer panel

## Estimated Impact Model

The hackathon requires a quantified impact model. PulseOps therefore separates:

- observed metrics in the live product UI
- estimated business impact in submission materials and pitch

Use the following note anywhere you present these numbers:

> These are benchmark-based estimates for judging and business modeling, not measured accounting outcomes from a production deployment.

### Onboarding Assumptions

- manual onboarding effort: `4.5 hours` per hire
- blended operations cost: `INR 1,500/hour`
- monthly hiring volume: `30 hires/month`

Back-of-envelope math:

- `4.5 hours x INR 1,500 = INR 6,750` estimated cost per manual onboarding
- `INR 6,750 x 30 = INR 202,500/month`
- `INR 202,500 x 12 = INR 2,430,000/year`

### Meeting Assumptions

- `40%` of action items are lost or delayed without structured follow-through
- `INR 2,500` conservative value per recovered task
- `4 meetings/month` with at least `4 clear action items` each

Back-of-envelope math:

- `4 tasks x 40% = 1.6` additional tasks recovered per meeting
- `1.6 x INR 2,500 = INR 4,000` value unlocked per meeting
- `INR 4,000 x 4 = INR 16,000/month`
- `INR 16,000 x 12 = INR 192,000/year`

### SLA Assumptions

- avoided cost per material breach: `INR 82,000`
- `200 approvals/month`
- breach rate without automation: `8%`
- breach rate with automation: `0.5%`

Back-of-envelope math:

- `200 x (8% - 0.5%) = 15` breaches prevented per month
- `15 x INR 82,000 = INR 1,230,000/month`
- `INR 1,230,000 x 12 = INR 14,760,000/year`

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in the values you want to use.

Minimum mock-mode setup:

```env
GEMINI_API_KEY=your_key_here
USE_REAL_APIS=false
```

Optional live integrations:

```env
SLACK_WEBHOOK_URL=...
JIRA_BASE_URL=...
JIRA_EMAIL=...
JIRA_API_TOKEN=...
GOOGLE_CALENDAR_ID=...
GOOGLE_SHEETS_ID=...
GOOGLE_SERVICE_ACCOUNT_JSON=...
TRELLO_API_KEY=...
TRELLO_TOKEN=...
TRELLO_BOARD_ID=...
```

Set:

```env
USE_REAL_APIS=true
```

to enable live routing where credentials are present.

## Run

```bash
streamlit run main.py
```

## Run With Docker

### Docker Compose

```bash
docker compose up --build
```

The container serves PulseOps at:

```text
http://localhost:8501
```

Docker Compose uses:

- `.env` for environment variables
- a named Docker volume for the SQLite audit ledger

### Notes For Live Google Integrations

If you want Google Calendar or Google Sheets to work inside Docker, the service-account JSON must also be available inside the container.

The simplest approach is:

- keep local development on the host machine for Google-integrated demos, or
- mount your service-account file into the container and set `GOOGLE_SERVICE_ACCOUNT_JSON` to the in-container path

Example container path:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=/app/secrets/service_account.json
```

## Recommended Demo Flow

### Demo 1: Onboarding

Use:

```text
Onboard new employee EMP-2026-001 starting Monday
```

Show:

- Orchestrator planning the workflow
- OnboardAgent executing steps
- JIRA failure and recovery path
- Ticket monitor auto-handoff
- thought chain and audit log
- observed metrics and auditability

### Demo 2: Meeting Workflow

Use:

```text
Process Platform Engineering Sync meeting transcript
```

Show:

- transcript parsing
- task creation
- ambiguity flagging
- no guessing policy

### Demo 3: SLA Recovery

Use:

```text
SLA breach on PROC-4821 requires immediate rerouting
```

Show:

- breach detection
- delegate lookup
- reroute action
- compliance explanation

## Submission Assets

- architecture document: [`ARCHITECTURE_AND_IMPACT.md`](ARCHITECTURE_AND_IMPACT.md)
- demo runbook: [`DEMO_CHECKLIST.md`](DEMO_CHECKLIST.md)
- pitch script: [`PITCH_SCRIPT.md`](PITCH_SCRIPT.md)

## Real API Notes

Best live demo path:

1. Slack webhook
2. Google Calendar
3. Trello

JIRA is supported, but user creation endpoints can be restricted depending on tenant permissions, so Slack is the safest first live integration for a demo.

## Safety and Resilience

- agents never call APIs directly without graceful error handling
- real API failures degrade to mock behavior where supported
- audit records include `api_source`
- onboarding continues even after JIRA failure
- ambiguous meeting ownership is flagged, not guessed

## Verification

You can run a quick syntax check with:

```bash
python -m py_compile main.py config.py tools\real_apis.py tools\api_router.py agents\react_engine.py agents\onboard_agent.py agents\meeting_agent.py agents\sla_agent.py utils\impact_calculator.py
```

## License

Hackathon project. Add your preferred license before external distribution.
