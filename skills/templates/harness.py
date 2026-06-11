"""Bounded orchestrator for the zero-dependency Python agent harness.

Integrates the nine components into a single while-loop. Live integration
happens through a single seam — ``model_turn`` — so the harness module
stays dependency-free; the caller wires in an LLM client.

Run modes:
    py harness/harness.py --mock --goal "..."          # scripted 4-iteration demo
    py harness/harness.py --goal "..." --adapter mod:fn # live, see README

Live adapter contract:
    fn(messages: list[dict]) -> dict with keys:
        role:      "assistant"
        content:   str
        tool_call: {"name": str, "args": dict} | None
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Make sibling modules importable whether run as ``py harness/harness.py`` or
# ``py -m harness.harness`` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from context_manager import ContextManager
from hooks import HookRegistry
from persistence import SessionLogger
from prompt_assembly import PromptAssembler
from subagent import SubAgentRunner
from tool_registry import Tool, ToolRegistry, register_builtins

ModelTurn = Callable[[List[Dict[str, str]]], Dict[str, Any]]


class Harness:
    """Bounded orchestrator. Owns the while loop and ties the nine components together."""

    def __init__(
        self,
        workspace_dir: Union[str, Path],
        session_id: str = "main_session",
        permission_mode: str = "WORKSPACE_WRITE",
        trusted_workspace: bool = True,
        max_iterations: int = 10,
        is_mock: bool = False,
        model_turn: Optional[ModelTurn] = None,
    ) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.session_id = session_id
        self.permission_mode = permission_mode
        self.trusted_workspace = trusted_workspace
        self.max_iterations = max_iterations
        self.is_mock = is_mock
        self._model_turn_fn = model_turn

        self.logger = SessionLogger(self.workspace_dir / ".harness" / f"{session_id}.jsonl")
        self.registry = ToolRegistry()
        self.hooks = HookRegistry()
        self.assembler = PromptAssembler()

        register_builtins(self.registry)

        self.base_system_prompt = (
            "You are an AI coding assistant. You must read and edit files in the workspace "
            "to achieve the user's goal. Always verify your changes before finishing."
        )

    # --- integration seam --------------------------------------------------- #

    def _model_turn(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Single integration point for a real LLM.

        Override this method in a subclass, or pass ``model_turn=`` to the
        constructor. The returned dict must contain ``role``, ``content`` and
        either ``tool_call`` (a ``{"name", "args"}`` dict) or ``None``.
        """
        if self._model_turn_fn is not None:
            return self._model_turn_fn(messages)
        raise NotImplementedError(
            "Live mode requires either --mock or a model_turn adapter.\n"
            "Provide one via Harness(model_turn=callable) or by subclassing "
            "and overriding _model_turn(messages)."
        )

    # --- lifecycle ---------------------------------------------------------- #

    def setup_hooks(self) -> None:
        def pre_hook_log(tool_name: str, args: Dict[str, Any]):
            print(f" -> [Pre-Hook] Intercepting call: {tool_name} with args {args}")
            return True, args

        def post_hook_log(tool_name: str, result: str):
            print(f" -> [Post-Hook] Logged execution of {tool_name}")

        self.hooks.register_pre_hook(pre_hook_log)
        self.hooks.register_post_hook(post_hook_log)

    def _register_spawn_tool(self) -> None:
        def spawn_subagent_handler(args: Dict[str, Any]) -> str:
            name = args.get("name", "sub-worker")
            task = args.get("task", "")
            allowed = args.get("allowed_tools", ["read_file"])
            sub_prompt = args.get("system_prompt", "Solve the task.")
            sub_max_iter = int(args.get("max_iterations", 5))

            runner = SubAgentRunner(
                name=name,
                base_registry=self.registry,
                allowed_tools=allowed,
                system_prompt=sub_prompt,
                workspace_dir=self.workspace_dir,
                parent_session_id=self.session_id,
                model_turn=self._model_turn_fn,
                max_iterations=sub_max_iter,
            )
            return runner.execute_task(task, self.permission_mode)

        self.registry.register(Tool(
            name="spawn_subagent",
            description=("Spawns an isolated sub-agent. Args: "
                         "{'name': str, 'task': str, 'allowed_tools': [str], "
                         "'system_prompt': str, 'max_iterations': int}"),
            required_permission="WORKSPACE_WRITE",
            handler=spawn_subagent_handler,
        ))

    # --- main loop ---------------------------------------------------------- #

    def run(self, goal: str) -> Dict[str, Any]:
        """Drive the while loop until the model signals done or the cap fires.

        Returns a small summary dict so callers can branch on exit reason.
        """
        print("=" * 60)
        print(f"Initializing Agent Harness in: {self.workspace_dir}")
        print(f"Permission Mode: {self.permission_mode}")
        print(f"Trusted Workspace: {self.trusted_workspace}")
        print(f"Mode: {'MOCK' if self.is_mock else 'LIVE'}")
        print("=" * 60)

        self.setup_hooks()
        self._register_spawn_tool()

        # 1. Replay history
        print("\nReplaying session history to restore state...")
        past_events = self.logger.replay_events()
        history: List[Dict[str, str]] = []
        if past_events:
            print(f"Found {len(past_events)} saved events. Restoring...")
            for event in past_events:
                data = event.get("data", {})
                if "role" in data and "content" in data:
                    history.append({"role": data["role"], "content": data["content"]})
        else:
            print("No previous state found. Starting a fresh session.")

        # 2. System prompt + goal
        system_prompt = self.assembler.assemble(self.base_system_prompt, self.workspace_dir)
        if not any(msg.get("role") == "system" for msg in history):
            history.insert(0, {"role": "system", "content": system_prompt})
        history.append({"role": "user", "content": goal})

        # 3. Context budget
        max_tokens = 1000 if self.is_mock else 100000
        context_mgr = ContextManager(max_tokens=max_tokens)

        # 4. While loop
        iteration = 0
        exit_reason = "iteration_cap"
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- [Iteration {iteration}/{self.max_iterations}] ---")

            if context_mgr.should_compact(history):
                print("[Context Manager] Threshold exceeded. Compacting history...")
                history = context_mgr.compact(history)
                self.logger.append_event(
                    "compaction",
                    {"role": "system", "content": "Context compacted."},
                )

            print(f"Context size: {context_mgr.calculate_total_tokens(history)} "
                  f"/ {context_mgr.max_tokens} estimated tokens.")

            # Decide next action
            if self.is_mock:
                tool_name, tool_args, finished = self._simulate_mock_turn(iteration, goal)
                assistant_content = (
                    f"[mock] iteration {iteration} -> {tool_name or '<done>'}"
                )
            else:
                response = self._model_turn(history)
                self.logger.append_event(
                    "model_turn",
                    {"role": "assistant", "content": response.get("content", "")},
                )
                tool_call = response.get("tool_call")
                assistant_content = response.get("content", "")
                if tool_call is None:
                    finished = True
                    tool_name, tool_args = "", {}
                else:
                    finished = False
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {}) or {}

            if finished:
                print(f"\n[Agent] Goal achieved or model signaled done. {assistant_content}")
                self.logger.append_event(
                    "done", {"role": "assistant", "content": assistant_content},
                )
                exit_reason = "done"
                break

            print(f"LLM decided to call tool: {tool_name}")

            # Pre-tool hook
            allowed, hook_res = self.hooks.dispatch_pre_hooks(
                tool_name, tool_args, self.trusted_workspace
            )
            if not allowed:
                result = f"Blocked by Pre-tool Hook: {hook_res}"
            else:
                actual_args = hook_res if isinstance(hook_res, dict) else tool_args
                result = self.registry.check_and_execute(
                    tool_name=tool_name,
                    args=actual_args,
                    session_permission=self.permission_mode,
                    interactive=True,
                )

            print(f"Tool Execution Output:\n{result}")

            # Post-tool hook
            self.hooks.dispatch_post_hooks(tool_name, result, self.trusted_workspace)

            # Memory: append both sides
            history.append({"role": "assistant", "content": assistant_content
                            + f"\nCalling tool {tool_name} with {tool_args}"})
            history.append({"role": "user", "content": result})
            self.logger.append_event(
                "tool_call",
                {"role": "assistant", "content": f"{tool_name} {tool_args}"},
            )
            self.logger.append_event(
                "tool_result", {"role": "user", "content": result},
            )

        if exit_reason == "iteration_cap":
            print(f"\n[Agent] Hit iteration cap of {self.max_iterations}.")
            self.logger.append_event(
                "cap_hit",
                {"role": "system", "content": f"Iteration cap {self.max_iterations} hit."},
            )

        print("\nSession finished.")
        return {
            "exit_reason": exit_reason,
            "iterations": iteration,
            "session_id": self.session_id,
            "log_path": str(self.logger.log_path),
        }

    # --- mock simulation ---------------------------------------------------- #

    def _simulate_mock_turn(
        self, iteration: int, goal: str
    ) -> Tuple[str, Dict[str, Any], bool]:
        if iteration == 1:
            return (
                "spawn_subagent",
                {
                    "name": "explorer-subagent",
                    "task": "Find directory structures",
                    "allowed_tools": ["read_file"],
                    "system_prompt": "You are exploring the filesystem.",
                    "max_iterations": 2,
                },
                False,
            )
        if iteration == 2:
            return (
                "write_file",
                {
                    "path": str(self.workspace_dir / "calculator.py"),
                    "content": (
                        "class Calculator:\n"
                        "    def add(self, a, b):\n"
                        "        return a + b\n"
                    ),
                },
                False,
            )
        if iteration == 3:
            return (
                "run_shell",
                {"command": f'"{sys.executable}" -m py_compile calculator.py'},
                False,
            )
        return "", {}, True


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _load_adapter(spec: str) -> ModelTurn:
    """Load a callable from ``module.path:attribute``."""
    if ":" not in spec:
        raise SystemExit(
            f"--adapter must be 'module.path:callable', got {spec!r}"
        )
    mod_name, attr = spec.split(":", 1)
    module = importlib.import_module(mod_name)
    fn = getattr(module, attr, None)
    if not callable(fn):
        raise SystemExit(f"{spec!r} is not callable")
    return fn


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Python agent harness.")
    parser.add_argument("--mock", action="store_true",
                        help="Run the scripted 4-iteration mock loop.")
    parser.add_argument("--goal", default="Set up project files",
                        help="The goal to drive the loop with.")
    parser.add_argument("--workspace", default=".", help="Workspace path.")
    parser.add_argument("--session-id", default="main_session")
    parser.add_argument("--max-iterations", type=int, default=10)
    parser.add_argument(
        "--adapter",
        help=("Live-mode LLM adapter as 'module.path:callable'. "
              "The callable receives the message list and returns "
              "{'role','content','tool_call'}. Ignored when --mock is set."),
    )
    args = parser.parse_args(argv)

    model_turn = None
    if not args.mock and args.adapter:
        model_turn = _load_adapter(args.adapter)

    harness = Harness(
        workspace_dir=args.workspace,
        session_id=args.session_id,
        max_iterations=args.max_iterations,
        is_mock=args.mock,
        model_turn=model_turn,
    )
    summary = harness.run(goal=args.goal)
    print(f"\nSummary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
