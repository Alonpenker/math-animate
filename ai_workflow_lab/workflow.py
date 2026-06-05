from pathlib import Path

from langgraph.graph import END, StateGraph

from lab_logging import LabLog
from nodes import NODE_SPECS
from runtime.context import ExperimentContext
from settings import MAX_ATTEMPTS
from workflow_state import (
    NodeName,
    WorkflowState,
    initial_state,
    workflow_recursion_limit,
)


def run_experiment(
    *,
    request_path: Path,
    name: str | None = None,
    provided_plan_path: Path | None = None,
    e2e: bool = False,
) -> Path:
    ctx = ExperimentContext.create(
        request_path=request_path,
        name=name,
        provided_plan_path=provided_plan_path,
        e2e=e2e,
    )
    graph = build_graph(ctx)
    compiled = graph.compile()
    recursion_limit = workflow_recursion_limit(MAX_ATTEMPTS)

    try:
        compiled.invoke(
            initial_state(ctx.request_text),
            config={"recursion_limit": recursion_limit},
        )
    except Exception as exc:
        ctx.run_logger.error(LabLog(
            operation="experiment",
            event="Experiment failed",
        ), exc_info=exc)
        ctx.write_summary({
            "status": "error",
            "error": str(exc),
            "run_dir": str(ctx.files.run_dir),
        })
        raise
    return ctx.files.run_dir


def build_graph(ctx: ExperimentContext) -> StateGraph:
    graph = StateGraph(WorkflowState)
    for spec in NODE_SPECS:
        graph.add_node(spec.name, spec.factory(ctx, spec.name))

    graph.set_entry_point(NodeName.GENERATE_PLAN)
    graph.add_edge(NodeName.GENERATE_PLAN, NodeName.LOAD_STATIC_KNOWLEDGE)
    graph.add_edge(NodeName.LOAD_STATIC_KNOWLEDGE, NodeName.GENERATE_CODE_PLAN)
    graph.add_edge(NodeName.GENERATE_CODE_PLAN, NodeName.GENERATE_CODE)
    graph.add_edge(NodeName.GENERATE_CODE, NodeName.VERIFY)
    graph.add_conditional_edges(NodeName.VERIFY, route_after_verify)
    graph.add_edge(NodeName.FIX_CODE, NodeName.VERIFY)
    graph.add_edge(NodeName.RENDER, END)
    graph.add_edge(NodeName.FAIL, END)
    return graph


def route_after_code_qa(state: WorkflowState) -> NodeName:
    verification = state["verification"]
    if verification.passed:
        return NodeName.RENDER
    if not verification.fixable:
        return NodeName.FAIL
    if state["attempt"] >= MAX_ATTEMPTS:
        return NodeName.FAIL
    return NodeName.FIX_CODE


def route_after_verify(state: WorkflowState) -> NodeName:
    verification = state["verification"]
    if verification.passed:
        return NodeName.RENDER
    if not verification.fixable:
        return NodeName.FAIL
    if state["attempt"] >= MAX_ATTEMPTS:
        return NodeName.FAIL
    return NodeName.FIX_CODE
