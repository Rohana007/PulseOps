"""Shared LangGraph ReAct execution helper used by PulseOps specialist agents."""

from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from tools.audit_ledger import log_action

load_dotenv()


def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1,
    )


def _extract_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = str(block.get("text", "")).strip()
                if text:
                    return text
    return ""


def _status_from_result(result_data: object) -> str:
    if not isinstance(result_data, dict):
        return "SUCCESS"
    raw = json.dumps(result_data).lower()
    raw_status = str(result_data.get("status", "success")).lower()
    if raw_status == "error" or '"status": "error"' in raw:
        return "ERROR"
    if "ticket_created" in raw or "rerouted" in raw or "escalat" in raw or "ticket" in raw:
        return "ESCALATED"
    if "flag" in raw:
        return "FLAGGED"
    if "retry" in raw:
        return "RETRY"
    return "SUCCESS"


def run_react_loop(
    goal: str,
    tools: list,
    workflow_id: str,
    agent_name: str,
    max_steps: int = 12,
) -> dict:
    """
    Run a specialist agent via LangGraph ReAct and log each visible step.
    """
    llm = get_llm()
    system_prompt = f"""
You are PulseOps specialist agent: {agent_name}
You are part of a multi-agent system supervised by an Orchestrator.

Rules:
1. Complete ALL tasks in the goal and never stop early
2. If a tool fails once, retry exactly once before escalating
3. Never guess ambiguous ownership and instead flag it
4. If one task fails or is escalated, continue all remaining tasks
5. Before each tool call, write one concise reasoning paragraph that explains why
6. When all tasks are done, stop calling tools and summarize outcomes
7. Do not exceed {max_steps} tool calls
""".strip()

    agent = create_react_agent(llm, tools, state_modifier=system_prompt)

    try:
        result = agent.invoke({"messages": [HumanMessage(content=goal)]})
    except Exception as exc:
        return {
            "thought_chain": [],
            "steps_completed": 0,
            "steps_escalated": 0,
            "steps_flagged": 0,
            "steps_errored": 1,
            "total_steps": 0,
            "final_message": f"Agent error: {exc}",
            "error": str(exc),
        }

    messages = result.get("messages", [])
    thought_chain: list[dict] = []
    step = 0
    pending_thought = ""

    for msg in messages:
        if isinstance(msg, AIMessage):
            visible_text = _extract_text(msg.content)
            if visible_text:
                pending_thought = visible_text
            tool_calls = getattr(msg, "tool_calls", None) or []
            for tool_call in tool_calls:
                step += 1
                thought = pending_thought or (
                    f"Deciding to call {tool_call['name']} based on current state."
                )
                thought_chain.append(
                    {
                        "step": step,
                        "thought": thought,
                        "action": tool_call["name"],
                        "params": tool_call.get("args", {}),
                        "status": "ACTING",
                        "result": "",
                        "escalated": False,
                        "api_source": "UNKNOWN",
                    }
                )
                pending_thought = ""
        elif isinstance(msg, ToolMessage) and thought_chain:
            last = thought_chain[-1]
            try:
                result_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
            except Exception:
                result_data = {"raw": str(msg.content)}
            result_str = json.dumps(result_data, default=str)[:400]
            status = _status_from_result(result_data)
            api_source = (
                str(result_data.get("_source", "UNKNOWN"))
                if isinstance(result_data, dict)
                else "UNKNOWN"
            )
            last["result"] = result_str
            last["status"] = status
            last["escalated"] = status in {"ESCALATED", "ERROR"}
            last["api_source"] = api_source

            log_action(
                workflow=workflow_id,
                agent=agent_name,
                step=last["step"],
                thought=last["thought"],
                action=f"Called {last['action']}",
                tool_called=last["action"],
                result=result_str,
                status=status,
                escalated=last["escalated"],
                confidence=0.9,
                api_source=api_source,
            )

    final_message = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_message = _extract_text(msg.content) or str(msg.content)
                break

    return {
        "thought_chain": thought_chain,
        "steps_completed": len([t for t in thought_chain if t["status"] == "SUCCESS"]),
        "steps_escalated": len([t for t in thought_chain if t["status"] in {"ESCALATED", "ERROR"}]),
        "steps_flagged": len([t for t in thought_chain if t["status"] == "FLAGGED"]),
        "steps_errored": len([t for t in thought_chain if t["status"] == "ERROR"]),
        "total_steps": len(thought_chain),
        "final_message": final_message,
        "raw_messages": messages,
    }
