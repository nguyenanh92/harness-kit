"""Spawn-Restrict-Collect sub-agent runner.

Enforces the single-level fork invariant: children copy only the parent's
allowed tools and never receive ``spawn_subagent``. Each child writes its
own JSONL log under the parent's ``.harness/`` directory.

A real model_turn callable drives the loop; if none is provided the runner
falls back to a deterministic mock that exits after one read-only probe so
the loop machinery is still exercised in tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from persistence import SessionLogger
from tool_registry import ToolRegistry

ModelTurn = Callable[[List[Dict[str, str]]], Dict[str, Any]]


class SubAgentRunner:
    """A child agent with a restricted registry and its own JSONL log."""

    def __init__(
        self,
        name: str,
        base_registry: ToolRegistry,
        allowed_tools: List[str],
        system_prompt: str,
        workspace_dir: Optional[Union[str, Path]] = None,
        parent_session_id: str = "main_session",
        model_turn: Optional[ModelTurn] = None,
        max_iterations: int = 5,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self._model_turn = model_turn

        # Single-level fork: copy explicitly allowed tools, omit spawn.
        self.registry = ToolRegistry()
        for tool_name in allowed_tools:
            if tool_name == "spawn_subagent":
                continue
            tool = base_registry.get_tool(tool_name)
            if tool:
                self.registry.register(tool)

        workspace = Path(workspace_dir).resolve() if workspace_dir else Path.cwd()
        log_dir = workspace / ".harness" / parent_session_id
        log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = SessionLogger(log_dir / f"{name}.jsonl")

    # ------------------------------------------------------------------ #
    # Default deterministic mock (no live adapter)
    # ------------------------------------------------------------------ #

    def _mock_turn(self, iteration: int) -> Dict[str, Any]:
        """One read-only probe, then signal done."""
        if iteration == 1 and self.registry.get_tool("read_file"):
            return {
                "role": "assistant",
                "content": f"[mock subagent {self.name}] probing filesystem",
                "tool_call": {"name": "read_file", "args": {"path": "."}},
            }
        return {
            "role": "assistant",
            "content": (
                f"Sub-agent '{self.name}' completed task. "
                f"Tools used: {sorted(self.registry._tools.keys())}"
            ),
            "tool_call": None,
        }

    # ------------------------------------------------------------------ #
    # Bounded loop
    # ------------------------------------------------------------------ #

    def execute_task(self, goal: str, parent_permission: str) -> str:
        print(f"\n[SUB-AGENT] '{self.name}' starting work on: '{goal}'")
        print(f"[SUB-AGENT] System prompt: {self.system_prompt[:60]}...")
        print(f"[SUB-AGENT] Allowed tools: {sorted(self.registry._tools.keys())}")

        history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": goal},
        ]
        self.logger.append_event(
            "subagent_start",
            {"role": "system", "content": f"{self.name} :: {goal}"},
        )

        final_content = ""
        for iteration in range(1, self.max_iterations + 1):
            if self._model_turn is not None:
                response = self._model_turn(history)
            else:
                response = self._mock_turn(iteration)

            content = response.get("content", "")
            self.logger.append_event(
                "subagent_turn", {"role": "assistant", "content": content}
            )
            history.append({"role": "assistant", "content": content})

            tool_call = response.get("tool_call")
            if tool_call is None:
                final_content = content
                break

            name = tool_call.get("name", "")
            args = tool_call.get("args", {}) or {}
            result = self.registry.check_and_execute(
                tool_name=name,
                args=args,
                session_permission=parent_permission,
                interactive=False,
            )
            self.logger.append_event(
                "subagent_tool", {"role": "user", "content": f"{name} -> {result[:200]}"}
            )
            history.append({"role": "user", "content": result})
        else:
            final_content = (
                f"Sub-agent '{self.name}' hit iteration cap of {self.max_iterations}."
            )
            self.logger.append_event(
                "subagent_cap",
                {"role": "system", "content": final_content},
            )

        print(f"[SUB-AGENT] '{self.name}' finished.")
        return final_content or f"Sub-agent '{self.name}' completed without output."
