import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Union, Tuple

# Relative imports to make it a self-contained module
from .persistence import SessionLogger
from .context_manager import ContextManager
from .tool_registry import ToolRegistry, register_builtins, Tool
from .hooks import HookRegistry
from .prompt_assembly import PromptAssembler
from .subagent import SubAgentRunner

class Harness:
    """
    The main orchestrator class representing the Agent Harness.
    Integrates the 9 core components into a cohesive, resilient loop.
    """
    def __init__(
        self,
        workspace_dir: Union[str, Path],
        session_id: str = "main_session",
        permission_mode: str = "WORKSPACE_WRITE",
        trusted_workspace: bool = True,
        max_iterations: int = 10,
        is_mock: bool = False
    ):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.permission_mode = permission_mode
        self.trusted_workspace = trusted_workspace
        self.max_iterations = max_iterations
        self.is_mock = is_mock
        
        # Initialize subsystems
        self.logger = SessionLogger(self.workspace_dir / ".harness" / f"{session_id}.jsonl")
        self.registry = ToolRegistry()
        self.hooks = HookRegistry()
        self.assembler = PromptAssembler()
        
        # Register default tools
        register_builtins(self.registry)
        
        # Setup base system prompt
        self.base_system_prompt = (
            "You are an AI coding assistant. You must read and edit files in the workspace "
            "to achieve the user's goal. Always verify your changes before finishing."
        )

    def setup_hooks(self) -> None:
        """
        Sets up default lifecycle hooks for logging and security checks.
        """
        def pre_hook_log(tool_name: str, args: Dict[str, Any]):
            print(f" -> [Pre-Hook] Intercepting call: {tool_name} with args {args}")
            return True, args # Allow execution and pass args unchanged

        def post_hook_log(tool_name: str, result: str):
            print(f" -> [Post-Hook] Logged execution of {tool_name}")

        self.hooks.register_pre_hook(pre_hook_log)
        self.hooks.register_post_hook(post_hook_log)

    def run(self, goal: str) -> None:
        """
        Launches the primary execution loop to solve the user's goal.
        """
        print("=" * 60)
        print(f"Initializing Agent Harness in: {self.workspace_dir}")
        print(f"Permission Mode: {self.permission_mode}")
        print(f"Trusted Workspace: {self.trusted_workspace}")
        print("=" * 60)
        
        # 1. Setup Hooks
        self.setup_hooks()
        
        # 2. Replay Session History (State & Memory Persistence)
        print("\nReplaying session history to restore state...")
        past_events = self.logger.replay_events()
        history: List[Dict[str, str]] = []
        
        if past_events:
            print(f"Found {len(past_events)} saved events. Restoring...")
            for event in past_events:
                # Reconstruct prompt history from log
                data = event.get("data", {})
                if "role" in data and "content" in data:
                    history.append({"role": data["role"], "content": data["content"]})
        else:
            print("No previous state found. Starting a fresh session.")
            
        # 3. Assemble System Prompt
        system_prompt = self.assembler.assemble(self.base_system_prompt, self.workspace_dir)
        
        # Inject system prompt into history if starting fresh
        if not any(msg.get("role") == "system" for msg in history):
            history.insert(0, {"role": "system", "content": system_prompt})
            
        history.append({"role": "user", "content": goal})
        
        # 4. Context Budgeting Initialization
        # Set max_tokens low in mock mode to demonstrate compaction easily
        max_tokens = 1000 if self.is_mock else 100000
        context_mgr = ContextManager(max_tokens=max_tokens)
        
        # Register sub-agent spawning tool (Component 4)
        def spawn_subagent_handler(args: Dict[str, Any]) -> str:
            name = args.get("name", "sub-worker")
            task = args.get("task", "")
            allowed = args.get("allowed_tools", ["read_file"])
            sub_prompt = args.get("system_prompt", "Solve the task.")
            
            # Create runner
            runner = SubAgentRunner(name, self.registry, allowed, sub_prompt)
            # Run and return summary
            return runner.execute_task(task, self.permission_mode)
            
        self.registry.register(Tool(
            name="spawn_subagent",
            description="Spawns an isolated sub-agent. Args: {'name': 'str', 'task': 'str', 'allowed_tools': ['str'], 'system_prompt': 'str'}",
            required_permission="WORKSPACE_WRITE",
            handler=spawn_subagent_handler
        ))

        # 5. Outer While Loop (Component 1)
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- [Iteration {iteration}/{self.max_iterations}] ---")
            
            # Check context size and compact if needed
            if context_mgr.should_compact(history):
                print("[Context Manager] Threshold exceeded. Compacting history...")
                history = context_mgr.compact(history)
                # Log compaction event
                self.logger.append_event("compaction", {"role": "system", "content": "Context compacted."})
            
            print(f"Context size: {context_mgr.calculate_total_tokens(history)} / {context_mgr.max_tokens} estimated tokens.")
            
            # Call LLM (In standard run, this queries API. In mock run, we simulate turns)
            if self.is_mock:
                tool_name, tool_args, finished = self._simulate_mock_turn(iteration, goal)
            else:
                # Real LLM API calls would go here
                print("Harness is in live mode. Placholder for actual LLM response.")
                finished = True
                break
                
            if finished:
                print("\n[Agent] Goal achieved! Exiting loop.")
                break
                
            # Execute tool call
            print(f"LLM decided to call tool: {tool_name}")
            
            # Dispatch Pre-tool Hooks (Component 8)
            allowed, hook_res = self.hooks.dispatch_pre_hooks(tool_name, tool_args, self.trusted_workspace)
            if not allowed:
                result = f"Block by Pre-tool Hook: {hook_res}"
            else:
                # Use possibly modified args from hook
                actual_args = hook_res if isinstance(hook_res, dict) else tool_args
                
                # Check permissions & Execute tool (Component 9)
                result = self.registry.check_and_execute(
                    tool_name=tool_name,
                    args=actual_args,
                    session_permission=self.permission_mode,
                    interactive=True
                )
                
            print(f"Tool Execution Output:\n{result}")
            
            # Dispatch Post-tool Hooks (Component 8)
            self.hooks.dispatch_post_hooks(tool_name, result, self.trusted_workspace)
            
            # Save events to Disk (Memory Persistence - Component 6)
            assistant_content = f"Calling tool {tool_name} with {tool_args}"
            history.append({"role": "assistant", "content": assistant_content})
            history.append({"role": "user", "content": result})
            
            self.logger.append_event("assistant_turn", {"role": "assistant", "content": assistant_content})
            self.logger.append_event("tool_result", {"role": "user", "content": result})

        print("\nSession finished.")

    def _simulate_mock_turn(self, iteration: int, goal: str) -> Tuple[str, Dict[str, Any], bool]:
        """
        Generates simulated turns to showcase how the harness orchestrates tools.
        """
        if iteration == 1:
            # First turn: Spawn a sub-agent to check the directory structure
            return (
                "spawn_subagent", 
                {
                    "name": "explorer-subagent",
                    "task": "Find directory structures",
                    "allowed_tools": ["read_file"],
                    "system_prompt": "You are exploring the filesystem."
                }, 
                False
            )
        elif iteration == 2:
            # Second turn: Write a file (WORKSPACE_WRITE)
            return (
                "write_file", 
                {
                    "path": str(self.workspace_dir / "calculator.py"),
                    "content": "class Calculator:\n    def add(self, a, b):\n        return a + b\n"
                }, 
                False
            )
        elif iteration == 3:
            # Third turn: Execute a shell command to test syntax (dynamic evaluation)
            # This triggers a command classification check (safe vs unsafe)
            return (
                "run_shell",
                {
                    "command": f'"{sys.executable}" -m py_compile calculator.py'
                },
                False
            )
        else:
            # Done!
            return "", {}, True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Python Agent Harness.")
    parser.add_argument("--mock", action="store_true", help="Run in mock simulation mode.")
    parser.add_argument("--goal", type=str, default="Set up project files", help="The goal for the agent.")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace path.")
    
    args = parser.parse_args()
    
    # Run harness
    harness = Harness(workspace_dir=args.workspace, is_mock=args.mock)
    harness.run(goal=args.goal)
