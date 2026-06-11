# Tool Registry and Safety

Load when you are adding a tool, changing a permission rule, or designing a sub-agent boundary.

## Golden rules

1. **Fail closed.** A tool not in the registry cannot be called. A command the classifier does not recognize is escalated, not auto-allowed.
2. **Classify per call, not per tool.** A single `run_shell` tool covers `ls`, `git commit`, and `rm -rf` — the *string passed at call time* determines the permission level, not the tool's type.
3. **Single-level fork.** A parent may spawn a child sub-agent. A child must not be able to spawn another. Enforce this by removing `spawn_subagent` from the child's registry, not by a runtime check alone.
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

## Sub-agent fork boundary

Spawn-Restrict-Collect lifecycle:

1. **Spawn.** Build a *new* `ToolRegistry` for the child by copying entries the parent explicitly allows. Skip `spawn_subagent` unconditionally.
2. **Restrict.** Override the child's `permission_mode` to the minimum needed for its task. Pass a tight `system_prompt` that names the deliverable.
3. **Collect.** The child returns a single summary string. Discard its intermediate tool-call log from the parent's context; keep it only in the child's own JSONL log under `.harness/<parent>/<child>.jsonl`.

> Why the single-level invariant: if a child can fork, context costs are unbounded, and a runaway child can sit invisible to the parent's iteration cap. The cap belongs to the loop, not the agent tree.

## Hook trust gate (all-or-nothing)

Hooks are powerful — they can log, redact, veto, or rewrite arguments. They are also user-supplied code from a workspace the harness may not trust.

The rule: **if the workspace is not explicitly trusted, do not run *any* hooks**. Do not pick and choose "safe-looking" hooks. Trust is a per-workspace boolean, not a per-file decision.

Trust signals (any one is sufficient):
- The user has run `--trust` on the workspace.
- The workspace is under a path the user has globally trusted (e.g., `~/repos/`).
- The user approves a one-shot `input()` prompt at session start.

When untrusted, `hooks.py` short-circuits both `dispatch_pre_hooks` and `dispatch_post_hooks` and returns the unchanged arguments / no-op respectively. The harness still runs.

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
