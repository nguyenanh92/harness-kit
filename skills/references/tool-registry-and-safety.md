# Tool Registry and Safety

Load when you are adding a tool, changing a permission rule, or designing a sub-agent boundary.

## Golden rules

1. **Fail closed.** A tool not in the registry cannot be called. A command the classifier does not recognize is escalated, not auto-allowed.
2. **Classify per call, not per tool.** A single `run_shell` tool covers `ls`, `git commit`, and `rm -rf` — the *string passed at call time* determines the permission level, not the tool's type.
3. **Fork vs. subagent nesting.** *Forks* inherit the full conversation history and may not spawn further forks — single-level only. *Regular subagents* run in a fresh context and can nest up to 3 levels (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). Enforce the fork boundary by removing `spawn_subagent` from the fork child's registry; nestable subagents manage their own iteration cap.
4. **Manual gate by default.** Any escalation prompts the user via `input()`; auto-allow only when the workspace is explicitly trusted *and* the command is read-only.

## Permission levels

| Level             | Numeric | Examples                                       | Default action |
|-------------------|---------|------------------------------------------------|----------------|
| `READ_ONLY`       | 1       | `ls`, `cat`, `git status`, `git diff`, `grep`  | Auto-allowed   |
| `WORKSPACE_WRITE` | 2       | `mkdir`, `touch`, `git add`, `git commit`, `pytest`, `pip install --user` | Allowed in workspace-write mode; else prompt |
| `FULL_ACCESS`     | 3       | `rm -rf`, `sudo`, `curl`, `wget`, `shutdown`, `chmod` system paths | Blocked by default; interactive approval required |

The classifier returns the *highest* matching level. When in doubt about an unrecognized command, return `WORKSPACE_WRITE` (not `READ_ONLY`) — escalating wastes a prompt; silently auto-running a write does not.

## A worked classifier

```python
def classify_command(cmd: str) -> str:
    normalized = cmd.strip().lower()

    full_access_patterns = (
        "rm -rf", "sudo", "shutdown", "curl", "wget", "chmod 777",
        "dd if=", " > /dev/", " > /etc/",
    )
    if any(p in normalized for p in full_access_patterns):
        return "FULL_ACCESS"

    workspace_patterns = (
        "mkdir", "touch", "rm ", "mv ", "cp ", "git add", "git commit",
        "git push", "pip install", "npm install", "pytest", "py -m",
    )
    if any(p in normalized for p in workspace_patterns):
        return "WORKSPACE_WRITE"

    return "READ_ONLY"
```

Notes on the implementation in `tool_registry.py`:
- Substring match is good enough for the standard library; do not pull in a shell-parser dependency.
- Always normalize with `.lower()` first.
- The order of the checks matters — `FULL_ACCESS` patterns must run before `WORKSPACE_WRITE` patterns, because `rm` substring appears inside `rm -rf`.

## Permission modes

The 3-tier classifier (READ_ONLY / WORKSPACE_WRITE / FULL_ACCESS) decides the *cost* of a command. The **permission mode** decides what to *do* with that cost. Six modes:

| Mode | Behavior |
|------|----------|
| `default` | Prompt user for WORKSPACE_WRITE and FULL_ACCESS commands |
| `acceptEdits` | Auto-approve file edits; prompt for shell commands |
| `plan` | Read-only — no file writes or shell commands allowed |
| `dontAsk` | Deny sensitive actions instead of prompting (CI-safe) |
| `auto` | Model classifier decides; overrides only on ambiguous commands |
| `bypassPermissions` | Full access — critical-path guardrails still apply (see below) |

**6-step evaluation order** for each tool call:

1. **Hooks** — any registered hook may deny (exit code `2`)
2. **Deny rules** — explicit `denyRules` patterns block unconditionally
3. **Ask rules** → callback — `askRules` patterns prompt the user
4. **Permission mode** — the active mode determines default behavior
5. **Allow rules** — `allowRules` patterns bypass the mode check
6. **`canUseTool` callback** — final programmatic veto

**Scoped patterns** let you target specific argument shapes, not just tool names:

```
Bash(rm *)          # match rm with any argument
Edit(//secrets/**)  # block edits inside /secrets/
mcp__github__get_*  # allow all MCP GitHub read tools
```

**Critical paths are blocked in all modes** — including `bypassPermissions`. `rm` / `rmdir` on system directories (`/`, `/usr`, `C:\Windows`) is unconditionally refused regardless of mode.

## Sub-agent fork boundary

Spawn-Restrict-Collect lifecycle:

1. **Spawn.** Build a *new* `ToolRegistry` for the child by copying entries the parent explicitly allows. Skip `spawn_subagent` unconditionally.
2. **Restrict.** Override the child's `permission_mode` to the minimum needed for its task. Pass a tight `system_prompt` that names the deliverable.
3. **Collect.** The child returns a single summary string. Discard its intermediate tool-call log from the parent's context; keep it only in the child's own JSONL log under `.harness/<parent>/<child>.jsonl`.

> Why the single-level invariant: if a child can fork, context costs are unbounded, and a runaway child can sit invisible to the parent's iteration cap. The cap belongs to the loop, not the agent tree.

## Hook trust gate

Hook trust is resolved through a 7-scope hierarchy — see [Lifecycle and hooks](lifecycle-and-hooks.md) for the full table. The practical rule for the Python harness:

- Hooks from user settings (`~/.claude/settings.json`) run regardless of workspace trust.
- Hooks from project settings (`.claude/settings.json`) require a workspace trust decision.
- The `allowManagedHooksOnly` enterprise flag disables all non-managed hooks.

Do not allow per-hook trust decisions within a scope. If the workspace is untrusted, `hooks.py` must short-circuit both `dispatch_pre_hooks` and `dispatch_post_hooks` for that scope — selectively running "safe-looking" hooks from an untrusted workspace is the attack surface this model is designed to prevent.

## MCP tools (optional)

MCP servers expose tools that integrate into the registry under the `mcp__<server>__<tool>` namespace. From the dispatch perspective they are identical to built-in tools; the classifier and permission modes apply equally.

Additional rules for MCP tools:

- **Re-fetch on `notifications/tools/list_changed`** — MCP tool lists are dynamic; a cached list misses tools added mid-session.
- **Apply the same permission classification** — an MCP tool that shells out or touches the network must still be classified `FULL_ACCESS`.
- **Isolate the MCP client** — import the `mcp` SDK only in an adapter module outside `harness/`; keep the core dependency-free.
- **Document MCP tool availability for sub-agents** — if a fork child should not reach an MCP server, remove those tool entries from the child's registry.

See [MCP integration](mcp-integration.md) for the full integration guide.

## Adding a new tool: checklist

- [ ] Define a handler with signature `(args: dict) -> dict`.
- [ ] Register via `registry.register(Tool(name, description, required_permission, handler))`.
- [ ] If it shells out, add a rule to `classify_command`.
- [ ] If it touches the network, mark `required_permission = FULL_ACCESS`.
- [ ] If it should be unavailable to sub-agents, document it in `subagent.py`'s allowed-tools docstring.
- [ ] Add an eval case to `evals/evals.json`.

## Related references

- [Architecture principles](architecture-principles.md) — why the bounded loop matters here.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — the trust gate in detail.
- [Gotchas](gotchas.md) — `rm` inside `rm -rf`, hook timeout traps, fork explosions.
