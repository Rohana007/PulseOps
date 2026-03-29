# PulseOps

PulseOps is an autonomous multi-agent enterprise operations system built for the ET AI Hackathon 2026.
It handles onboarding, meeting follow-through, SLA recovery, and cross-agent handoffs with full auditability.

## What It Does

PulseOps is designed to solve three common enterprise workflow failures:

- New-hire onboarding gets delayed across HR, IT, Slack, JIRA, and calendar systems
- Meeting action items disappear because ownership is unclear or never tracked
- Approvals breach SLA because the assigned approver is unavailable

Instead of using brittle rules, PulseOps uses a LangGraph-based orchestrator and specialist agents that reason before acting, recover from failures, hand off work automatically, and explain every decision.

## Why It’s Different

- ReAct architecture: each agent reasons before each tool call
- Real multi-agent orchestration: the Orchestrator delegates to specialists
- Exception handling: JIRA failures trigger retry, escalation, and monitoring
- Audit-first design: every action is written to SQLite with thought + result
- Real or mock integrations: Slack, JIRA, Google Calendar, Google Sheets, and Trello can run live or fall back safely
- Ambiguity-safe behavior: the MeetingAgent never guesses unclear ownership

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
     Audit Ledger + Explainer + Impact Dashboard
```

## Project Structure

```text
pulseops/
├── .env
├── README.md
├── config.py
├── main.py
├── requirements.txt
├── agents/
│   ├── orchestrator.py
│   ├── react_engine.py
│   ├── onboard_agent.py
│   ├── meeting_agent.py
│   └── sla_agent.py
├── tools/
│   ├── api_router.py
│   ├── audit_ledger.py
│   ├── mock_apis.py
│   └── real_apis.py
└── utils/
    ├── explainer.py
    └── impact_calculator.py
```

## Core Components

### Orchestrator

[orchestrator.py](d:/et/pulseops/agents/orchestrator.py) is the supervisor.
It interprets the enterprise event, builds an execution plan with Gemini, activates specialist agents, and triggers downstream handoffs when needed.

### Specialist Agents

- [onboard_agent.py](d:/et/pulseops/agents/onboard_agent.py): provisions employee workflows across HR, Slack, JIRA, orientation scheduling, and welcome messaging
- [meeting_agent.py](d:/et/pulseops/agents/meeting_agent.py): parses transcript action items, creates tasks, and flags ambiguous ownership
- [sla_agent.py](d:/et/pulseops/agents/sla_agent.py): handles approval rerouting and ticket SLA monitoring

### ReAct Engine

[react_engine.py](d:/et/pulseops/agents/react_engine.py) runs the LangGraph ReAct loop, extracts the reasoning chain, logs tool outcomes, and records whether each tool call used a live integration or a mock.

### Routing Layer

[api_router.py](d:/et/pulseops/tools/api_router.py) decides whether to use:

- real APIs
- mock APIs
- mock fallback after a real API error

This keeps the app demo-safe while still supporting real integration wow-factor.

### Audit + Explainability

- [audit_ledger.py](d:/et/pulseops/tools/audit_ledger.py): append-only SQLite audit trail
- [explainer.py](d:/et/pulseops/utils/explainer.py): plain-English answer to “Why did you do that?”

### Business Value Layer

[impact_calculator.py](d:/et/pulseops/utils/impact_calculator.py) contains the benchmark-based business model used for submission materials and pitch math.
The live dashboard now prioritizes observed run metrics so the product UI stays factual during demos.

## UI Features

The Streamlit dashboard in [main.py](d:/et/pulseops/main.py) includes:

- premium dark control-room UI
- API connection status bar
- orchestration plan display
- agent execution timeline
- full thought chain view
- live audit ledger
- LIVE / MOCK / FALLBACK badges
- observed metrics dashboard
- notification log
- explainer panel

## Estimated Impact Model

The hackathon requires a quantified impact model. PulseOps therefore separates:

- observed metrics in the live product UI
- estimated business impact in submission materials and pitch

Use the following note anywhere you present these numbers:

> These are benchmark-based estimates for judging and business modeling, not measured accounting outcomes from a production deployment.

### Assumptions

#### Onboarding

- Manual onboarding effort: `4.5 hours` per hire
- Blended operations cost: `INR 1,500/hour`
- Monthly hiring volume: `30 hires/month`

Back-of-envelope math:

- `4.5 hours x INR 1,500 = INR 6,750` estimated cost per manual onboarding
- `INR 6,750 x 30 = INR 202,500/month`
- `INR 202,500 x 12 = INR 2,430,000/year`

Pitch line:

- PulseOps can reclaim roughly `INR 6,750` per hire in avoided manual operational effort, subject to team structure and process maturity.

#### Meeting Action Items

- Benchmark assumption: `40%` of action items are lost or delayed without structured follow-through
- Conservative value per recovered task: `INR 2,500`
- Example cadence: `4 meetings/month` with at least `4 clear action items` each

Back-of-envelope math:

- `4 tasks x 40% = 1.6` additional tasks recovered per meeting
- `1.6 x INR 2,500 = INR 4,000` value unlocked per meeting
- `INR 4,000 x 4 = INR 16,000/month`
- `INR 16,000 x 12 = INR 192,000/year`

Pitch line:

- PulseOps improves follow-through by turning meeting output into tracked work while explicitly flagging ambiguity instead of guessing.

#### SLA Recovery

- Conservative avoided penalty per material breach: `INR 82,000`
- Example operational volume: `200 approvals/month`
- Without automation breach rate assumption: `8%`
- With automation breach rate assumption: `0.5%`

Back-of-envelope math:

- `200 x (8% - 0.5%) = 15` breaches prevented per month
- `15 x INR 82,000 = INR 1,230,000/month`
- `INR 1,230,000 x 12 = INR 14,760,000/year`

Pitch line:

- PulseOps reduces approval gridlock by detecting breaches early, rerouting blocked approvals, and preserving a full compliance trail.

### Submission-Friendly Summary

If you need one compact impact block for the architecture document or slide deck, use:

- Onboarding: `INR 6,750` estimated operational effort saved per hire
- Meetings: higher completion and accountability through structured task creation and ambiguity flagging
- SLA: `INR 82,000` estimated avoided cost per prevented breach incident
- Combined business case: meaningful operational savings even before adding enterprise software replacement value

### Demo Guidance

In the live product demo:

- show observed metrics only
- describe the impact model verbally or in the README / deck
- state assumptions clearly if a judge asks how the numbers were derived

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

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

A quick syntax verification can be run with:

```bash
python -m py_compile main.py config.py tools\real_apis.py tools\api_router.py agents\react_engine.py agents\onboard_agent.py agents\meeting_agent.py agents\sla_agent.py utils\impact_calculator.py
```

## Pitch Summary

PulseOps targets Indian mid-market companies that cannot afford enterprise automation suites like ServiceNow but still need robust, auditable, exception-aware operations automation.

It is positioned as:

- much cheaper than enterprise workflow suites
- safer than brittle no-code automations
- more transparent than black-box copilots

## License

Hackathon project. Add your preferred license before external distribution.
