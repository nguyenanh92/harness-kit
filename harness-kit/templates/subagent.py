from typing import Dict, Any, List
from .tool_registry import ToolRegistry

class SubAgentRunner:
    """
    Spawns and runs sub-agents in isolation.
    Enforces the single-level execution boundary (no recursive forks allowed).
    """
    def __init__(
        self, 
        name: str, 
        base_registry: ToolRegistry, 
        allowed_tools: List[str], 
        system_prompt: str
    ):
        self.name = name
        self.system_prompt = system_prompt
        
        # Build restricted toolset registry
        self.registry = ToolRegistry()
        for tool_name in allowed_tools:
            # Fork restriction: Child cannot have spawning capability
            if tool_name == "spawn_subagent":
                continue
            tool = base_registry.get_tool(tool_name)
            if tool:
                self.registry.register(tool)

    def execute_task(self, goal: str, parent_permission: str) -> str:
        """
        Executes a task on behalf of the parent.
        Runs a mock/isolated loop using the restricted tool registry.
        """
        print(f"\n[SUB-AGENT] '{self.name}' starting work on: '{goal}'")
        print(f"[SUB-AGENT] System Prompt: {self.system_prompt[:60]}...")
        print(f"[SUB-AGENT] Allowed tools: {list(self.registry._tools.keys())}")
        
        # Simulated run of child loop
        # In a real environment, this would call LLM API with self.system_prompt
        # and self.registry tools, then run the while loop.
        
        # Here we mock a successful execution
        result_summary = (
            f"Sub-agent '{self.name}' successfully completed task: '{goal}'\n"
            f"Output: Verified files are in place."
        )
        
        print(f"[SUB-AGENT] '{self.name}' finished.")
        return result_summary
