import os
import subprocess
import re
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional

@dataclass
class Tool:
    name: str
    description: str
    required_permission: str  # "READ_ONLY", "WORKSPACE_WRITE", or "FULL_ACCESS"
    handler: Callable[[Dict[str, Any]], str]

class ToolRegistry:
    """
    A registry containing all tools available to the Agent.
    Implements security permission gates and dynamic command classification.
    """
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
        
    def get_descriptors(self) -> List[Dict[str, Any]]:
        """
        Returns a lightweight list of descriptors to inject into the LLM context.
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "required_permission": t.required_permission
            }
            for t in self._tools.values()
        ]

    def classify_command(self, cmd: str) -> str:
        """Classify a shell command string into a permission tier.

        Checked from most to least dangerous so longer specific patterns
        (e.g. 'rm -rf') are matched before shorter overlapping ones ('rm ').
        """
        normalized = cmd.strip().lower()

        # FULL_ACCESS: irreversible / system-level / network actions.
        # Recursive-delete patterns must come before bare 'rm ' below.
        _FULL_ACCESS = (
            "rm -rf", "rm -r",
            "sudo", "shutdown", "reboot",
            "curl ", "wget ",
            "chmod", "chown",
            "dd ",
            "mkfs", "fdisk",
        )
        if any(p in normalized for p in _FULL_ACCESS):
            return "FULL_ACCESS"

        # WORKSPACE_WRITE: local filesystem mutations (usually recoverable).
        _WORKSPACE_WRITE = (
            "rm ",          # single-file remove (after recursive patterns above)
            "mv ", "cp ",
            "truncate ",
            "mkdir", "touch",
            "git add", "git commit", "git merge", "git rebase",
            "pip install", "npm install", "yarn add",
        )
        if any(p in normalized for p in _WORKSPACE_WRITE):
            return "WORKSPACE_WRITE"

        return "READ_ONLY"

    def check_and_execute(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        session_permission: str,
        interactive: bool = True
    ) -> str:
        """
        Evaluates permissions, prompts for approval if necessary, and executes the tool.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found in registry."

        # Evaluate target permission level
        required = tool.required_permission
        
        # For shell execution, evaluate command dynamically
        if tool_name == "run_shell" and "command" in args:
            required = self.classify_command(args["command"])
            
        # Define hierarchy: READ_ONLY (1) < WORKSPACE_WRITE (2) < FULL_ACCESS (3)
        hierarchy = {"READ_ONLY": 1, "WORKSPACE_WRITE": 2, "FULL_ACCESS": 3}
        session_level = hierarchy.get(session_permission, 1)
        required_level = hierarchy.get(required, 1)

        # Gate Check
        if required_level > session_level:
            if interactive:
                # Prompt for interactive approval
                print(f"\n[SECURITY WARNING] Tool '{tool_name}' requires level '{required}' (Current session level: '{session_permission}').")
                print(f"Arguments: {args}")
                response = input("Do you want to authorize this execution? (y/N): ").strip().lower()
                if response != 'y':
                    return f"Execution Denied: User rejected permission escalation to '{required}'."
            else:
                return f"Execution Denied: Required permission level '{required}' exceeds session level '{session_permission}' in non-interactive mode."

        # Execute handler
        try:
            return tool.handler(args)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

# ==========================================
# Built-in Primitives (Zero-dependency)
# ==========================================

def read_file_handler(args: Dict[str, Any]) -> str:
    path = args.get("path")
    if not path:
        return "Error: Path parameter is required."
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error: Cannot read file: {str(e)}"

def write_file_handler(args: Dict[str, Any]) -> str:
    path = args.get("path")
    content = args.get("content", "")
    if not path:
        return "Error: Path parameter is required."
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Wrote file to '{path}'."
    except Exception as e:
        return f"Error: Cannot write file: {str(e)}"

def run_shell_handler(args: Dict[str, Any]) -> str:
    command = args.get("command")
    if not command:
        return "Error: Command parameter is required."
    try:
        # Run process with a timeout to avoid hangs
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30
        )
        output = result.stdout + result.stderr
        return f"Exit Code: {result.returncode}\nOutput:\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Process timed out after 30 seconds."
    except Exception as e:
        return f"Error running process: {str(e)}"

# Pre-register built-in primitives helper
def register_builtins(registry: ToolRegistry) -> None:
    registry.register(Tool(
        name="read_file",
        description="Reads contents of a file. Args: {'path': 'string'}",
        required_permission="READ_ONLY",
        handler=read_file_handler
    ))
    registry.register(Tool(
        name="write_file",
        description="Creates or overwrites a file. Args: {'path': 'string', 'content': 'string'}",
        required_permission="WORKSPACE_WRITE",
        handler=write_file_handler
    ))
    registry.register(Tool(
        name="run_shell",
        description="Executes a shell command. Args: {'command': 'string'}",
        required_permission="WORKSPACE_WRITE", # Evaluated dynamically
        handler=run_shell_handler
    ))
