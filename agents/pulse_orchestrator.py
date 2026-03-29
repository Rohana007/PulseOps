"""
PulseOps — Master orchestrator (LangGraph entrypoint).
Compiles the workflow graph and runs the selected scenario end-to-end.
"""

from graph.workflow_graph import build_workflow_app

_APP = None


def _get_app():
    global _APP
    if _APP is None:
        _APP = build_workflow_app()
    return _APP


def get_workflow_mermaid() -> str:
    """Mermaid diagram of the compiled graph (for docs / UI)."""
    return _get_app().get_graph().draw_mermaid()


def run_pulse_workflow(
    scenario_label: str,
    workflow_id: str,
    employee_id: str = "EMP-2026-001",
    approval_id: str = "PROC-4821",
) -> dict | None:
    """Invoke the LangGraph workflow; returns the dashboard payload dict or None."""
    app = _get_app()
    config = {"configurable": {"thread_id": workflow_id}}
    out = app.invoke(
        {
            "scenario": scenario_label,
            "workflow_id": workflow_id,
            "employee_id": employee_id,
            "approval_id": approval_id,
        },
        config,
    )
    result = out.get("result")
    return result if isinstance(result, dict) else None
