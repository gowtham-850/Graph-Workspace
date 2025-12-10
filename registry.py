"""Simple tool registry for helper utilities that nodes can call."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Callable[..., Any]:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' is not registered.")
        return tool

    def try_get(self, name: str) -> Optional[Callable[..., Any]]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Callable[..., Any]]:
        return dict(self._tools)


def _detect_smells(code: str) -> list[str]:
    """Very small heuristic-based smell detector."""
    smells: list[str] = []
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    if not lines:
        smells.append("No code provided.")
        return smells

    if any("TODO" in line or "FIXME" in line for line in lines):
        smells.append("Found TODO/FIXME markers.")
    if any(len(line) > 120 for line in lines):
        smells.append("Lines exceed 120 characters.")
    if sum(1 for line in lines if line.startswith("#")) > len(lines) * 0.5:
        smells.append("Comment density is unusually high.")
    if "print(" in code and "logging" not in code:
        smells.append("Uses print statements instead of logging.")
    return smells


def _estimate_length_complexity(code: str) -> int:
    """Rough complexity proxy based on line count."""
    return min(100, max(5, len([ln for ln in code.splitlines() if ln.strip()]) // 2))


def register_default_tools(tool_registry: ToolRegistry) -> None:
    tool_registry.register("detect_smells", _detect_smells)
    tool_registry.register("estimate_length_complexity", _estimate_length_complexity)