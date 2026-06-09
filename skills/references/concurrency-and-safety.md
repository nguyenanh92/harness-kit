# Concurrency and Safety in Agent Harnesses

This reference document details safety strategies, tool classification, and sub-agent isolation to protect the user's local system from destructive actions.

---

## 1. Permission Gating & Dynamic Classification

Static permissions (e.g., "this tool is read-only") are insufficient. For example, a `run_shell` tool can execute safe, read-only commands as well as destructive write commands.

### Dynamic Command Classifier
Before executing shell commands, the harness should parse the command string and classify it dynamically:

- **READ-ONLY**: Command is purely informational.
  - *Matches*: `ls`, `git status`, `git diff`, `pwd`, `cat`, `grep`, `find`.
  - *Action*: Executed automatically without approval.
- **WORKSPACE WRITE**: Command modifies the workspace.
  - *Matches*: `mkdir`, `touch`, `git add`, `git commit`, `python -m unittest`.
  - *Action*: Permitted if in workspace-write mode; otherwise prompts the user.
- **FULL ACCESS (RESTRICTED)**: Command interacts with external networks, modifies files outside the workspace, or performs destructive deletions.
  - *Matches*: `rm`, `curl`, `wget`, `sudo`, `shutdown`, `pip install`, `npm install`.
  - *Action*: Blocked by default; requires interactive console approval.

```python
# Conceptual classifier function
def classify_command(cmd: str) -> str:
    # Normalize command
    normalized = cmd.strip().lower()
    
    # Check for destructive keywords
    if any(k in normalized for k in ["rm -rf", "sudo", "shutdown", "curl", "wget"]):
        return "FULL_ACCESS"
        
    # Check for modification keywords
    if any(k in normalized for k in ["mkdir", "touch", "git add", "git commit", "pip", "npm"]):
        return "WORKSPACE_WRITE"
        
    # Default to read-only for inspection commands
    return "READ_ONLY"
```

---

## 2. Fork Boundary Constraints: Sub-Agent Isolation

When task complexity requires delegating work to a Sub-Agent, the harness must enforce strict boundary limits.

### The Single-Level Invariant (Fork Children Must Not Fork)
If a Sub-Agent can spawn its own sub-agents, context costs explode exponentially, and tracking running processes becomes untractable.

> [!CAUTION]
> **Enforce Single-Level Spawning:**
> A parent process can fork child sub-agents. However, the system prompt of the child sub-agent must strictly omit the `spawn_subagent` tool, or the execution engine must block any attempt at runtime.

### Spawn-Restrict-Collect Lifecycle:
1. **Spawn**: Create a separate conversation session with a clean, focused system prompt.
2. **Restrict**: Remove dangerous tools (e.g., shell access, subprocess execution) and restrict file modifications to a specific subdirectory or file list.
3. **Collect**: Once the child exits, return only its final output summary to the parent context, discarding the verbose intermediate chat history.

---

## 3. Lifecycle Hook Trust (All-or-Nothing Trust Gate)

Hooks are powerful for logging, telemetry, and security checks. However, running arbitrary hook scripts from an untrusted workspace (e.g., a cloned repository with custom hook files) is highly dangerous.

- **Trust Boundary**: If the workspace is marked as **untrusted** (e.g., the user hasn't explicitly run `trust` or approved the workspace), **all local hooks are skipped**. Do not attempt to run "safe-looking" hooks; execute only built-in, hardcoded validation checks.
- **Hook Isolation**: Hooks must run within the same timeout constraints as tools. If a pre-tool hook hangs, the harness must abort the tool execution.
