from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .engine import WorkflowEngine
from .models import (
    GraphCreateRequest,
    GraphCreateResponse,
    GraphRunRequest,
    GraphRunResult,
    GraphStateResponse,
)
from .registry import ToolRegistry, register_default_tools
from .workflows.code_review import build_code_review_workflow

app = FastAPI(title="Workflow Graph Engine", version="0.1.0")

tool_registry = ToolRegistry()
register_default_tools(tool_registry)
engine = WorkflowEngine(tool_registry)

# Available workflow factories; new workflows can be added here.
WORKFLOW_BUILDERS = {"code_review": build_code_review_workflow}


@app.on_event("startup")
async def ensure_default_graph() -> None:
    """Register the demo code review workflow on startup."""
    if not engine.has_graph("code_review"):
        engine.register_graph("code_review", build_code_review_workflow(tool_registry))


@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(payload: GraphCreateRequest) -> GraphCreateResponse:
    builder = WORKFLOW_BUILDERS.get(payload.workflow)
    if not builder:
        raise HTTPException(status_code=400, detail=f"Unknown workflow '{payload.workflow}'.")

    graph = builder(tool_registry)
    engine.register_graph(payload.graph_id, graph)
    return GraphCreateResponse(
        graph_id=payload.graph_id,
        start_node=graph.start_node,
        available_nodes=list(graph.nodes.keys()),
    )


@app.post("/graph/run", response_model=GraphRunResult)
async def run_graph(payload: GraphRunRequest) -> GraphRunResult:
    if not engine.has_graph(payload.graph_id):
        raise HTTPException(status_code=404, detail=f"Graph '{payload.graph_id}' is not registered.")

    run = await engine.run_graph(payload.graph_id, payload.initial_state)
    return GraphRunResult(
        run_id=run.run_id,
        graph_id=run.graph_id,
        final_state=run.state,
        logs=run.logs,
        status=run.status,
    )


@app.get("/graph/state/{run_id}", response_model=GraphStateResponse)
async def get_run_state(run_id: str) -> GraphStateResponse:
    run = engine.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    return GraphStateResponse(
        run_id=run.run_id,
        graph_id=run.graph_id,
        state=run.state,
        logs=run.logs,
        status=run.status,
        current_node=run.current_node,
    )