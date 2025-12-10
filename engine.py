"""Workflow engine with async node execution and simple graph/state management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Optional

from .registry import ToolRegistry


@dataclass
class NodeResult:
    """Return type for a node indicating the next node and an optional log message."""

    next_node: Optional[str] = None
    message: Optional[str] = None


NodeCallable = Callable[[dict, ToolRegistry, Callable[[str], None]], Awaitable[NodeResult]]


@dataclass
class GraphDefinition:
    start_node: str
    nodes: Dict[str, NodeCallable]


@dataclass
class GraphRun:
    run_id: str
    graph_id: str
    state: dict
    logs: list[str] = field(default_factory=list)
    status: str = "pending"
    current_node: Optional[str] = None


class WorkflowEngine:
    """In-memory workflow engine that supports branching and looping graphs."""

    def __init__(self, tool_registry: ToolRegistry):
        self.graphs: Dict[str, GraphDefinition] = {}
        self.runs: Dict[str, GraphRun] = {}
        self.tool_registry = tool_registry

    def register_graph(self, graph_id: str, graph: GraphDefinition) -> GraphDefinition:
        self.graphs[graph_id] = graph
        return graph

    def has_graph(self, graph_id: str) -> bool:
        return graph_id in self.graphs

    def get_run(self, run_id: str) -> Optional[GraphRun]:
        return self.runs.get(run_id)

    def _append_log(self, run: GraphRun, message: str) -> None:
        run.logs.append(message)

    def _logger(self, run: GraphRun) -> Callable[[str], None]:
        return lambda msg: self._append_log(run, msg)

    async def run_graph(self, graph_id: str, initial_state: Optional[dict] = None) -> GraphRun:
        if graph_id not in self.graphs:
            raise KeyError(f"Graph '{graph_id}' is not registered.")

        run_id = str(uuid.uuid4())
        run = GraphRun(
            run_id=run_id,
            graph_id=graph_id,
            state=dict(initial_state or {}),
            status="running",
        )
        self.runs[run_id] = run
        graph = self.graphs[graph_id]
        logger = self._logger(run)

        current = graph.start_node
        try:
            while current:
                run.current_node = current
                handler = graph.nodes.get(current)
                if handler is None:
                    logger(f"Node '{current}' not found; halting run.")
                    break

                logger(f"Executing node '{current}'")
                result = await handler(run.state, self.tool_registry, logger)

                if result.message:
                    logger(result.message)

                current = result.next_node

            run.status = "completed"
            run.current_node = None
            logger("Run completed.")
            return run
        except Exception as exc:  # noqa: BLE001
            run.status = "failed"
            logger(f"Run failed: {exc}")
            raise