"""Pydantic models used by the FastAPI layer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GraphCreateRequest(BaseModel):
    graph_id: str = Field(..., description="Unique identifier for the graph instance.")
    workflow: str = Field(
        "code_review",
        description="Name of the workflow to instantiate (defaults to the demo code review).",
    )


class GraphCreateResponse(BaseModel):
    graph_id: str
    start_node: str
    available_nodes: List[str]


class GraphRunRequest(BaseModel):
    graph_id: str = Field(..., description="Graph id to execute.")
    initial_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary JSON-serialisable payload passed as shared state.",
    )


class GraphRunResult(BaseModel):
    run_id: str
    graph_id: str
    final_state: Dict[str, Any]
    logs: List[str]
    status: str


class GraphStateResponse(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    logs: List[str]
    status: str
    current_node: Optional[str] = None
