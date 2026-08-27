# Lifecycle and Hooks

Load when bootstrapping a session, when wiring hooks, or when designing the restart story.

## Bootstrap stages

A session starts cold; the harness should bring up trust *gradually*, not flip a single switch:

1. **Minimal.** Load `harness.py`, register built-in tools, open the JSONL log. No hooks, no sub-agents, no shell. The agent can read files only.
2. **Verification.** Run `./init.sh` / `./init.ps1` once. If it fails, refuse to advance — a broken workspace must not graduate to writes.
3. **Workspace write.** Enable `WORKSPACE_WRITE` shell commands. The agent can now scaffold and run tests.
4. **Trusted.** Enable project-scoped hooks (requires workspace trust dialog; see the 7-scope hierarchy in the Trust gate section below) and `FULL_ACCESS` shell with interactive approval. Sub-agents become spawnable. User-scoped hooks (`~/.claude/settings.json`) are already active from stage 1 — they do not require workspace trust.

Most harnesses can skip stages 3 and 4 if the task only needs reads. The stages exist so escalation is *visible* — an agent that asks for full access should have explained why.

## The session log as restart contract

Restart is not a UI feature; it is a property of the JSONL log. Resuming a session is exactly:

```python
events = SessionLogger(log_path).replay_events()
context = reconstruct_messages(events)
iteration = max(e["iteration"] for e in events) + 1
active_feature = read_active_feature("feature_list.json")
```

If you cannot resume a session from its log alone, the log is missing events. Add them before you add anything else.

## Hook types

Five hook types are available, each targeting a different event surface:

| Type | Fires on | Typical use |
|------|----------|-------------|
| `command` | Shell / Bash tool calls | Audit, redact, veto destructive commands |
| `http` | Outbound HTTP / MCP requests | Rate-limit, log, inject auth headers |
| `mcp_tool` | MCP tool invocations | Namespace filtering, argument rewriting |
| `prompt` | User prompt submission | Pre-flight checks, token budget estimation |
| `agent` | Sub-agent spawn / stop events | Parental audit, resource accounting |

**Hooks run outside the context window.** They consume zero tokens — hook output is not injected into the conversation.

## Hook signatures

```python
PreHookFunc  = Callable[[str, dict], tuple[bool, Any]]   # (tool, args) -> (allow, args_or_reason)
PostHookFunc = Callable[[str, str], None]                # (tool, result) -> None
```

**Pre-tool hooks** can:
- Veto a call by returning `(False, "reason")`. The harness logs the veto and continues to the next iteration.
- Rewrite arguments by returning `(True, new_args)`. Useful for path normalization or secret redaction.
- Run synchronously only. Hooks share the tool's timeout; a hung hook fails the tool call.

**Post-tool hooks** are for telemetry, logging, and side-effect propagation. They cannot affect the tool's result — by the time they fire, the work is already done.

## Exit-code contract

Hook processes communicate disposition via exit code:

| Exit code | Meaning |
|-----------|---------|
| `0` | Proceed — allow the tool call |
| `2` | **Block** — veto the tool call; harness logs reason and continues loop |
| `1`, `3–N` | Non-blocking error — logged, execution continues (does NOT veto) |

Only exit code `2` vetoes. Using exit `1` to try to block a call is a silent no-op.

## Notable lifecycle events

Beyond pre/post-tool, the hook system emits these events:

- **`PreCompact`** — fires before context compaction; allows transcript archiving before the middle band is summarized away.
- **`SubagentStop`** — fires when a child sub-agent exits; useful for collecting results and cleaning up resources.
- **`FileChanged`** — fires after any file write; useful for triggering lint or test runs.
- **`InstructionsLoaded`** — fires after `CLAUDE.md` / `AGENTS.md` is loaded; useful for validation.

## Trust gate

The hook trust model uses a **7-scope hierarchy** (not a single flag). Each scope adds or restricts what can run:

| Scope | Trust level | Override |
|-------|-------------|----------|
| Managed policy (`~/.claude/managed-settings.json`) | Admin-controlled; always runs | `allowManagedHooksOnly` enterprise flag blocks all other scopes |
| User settings (`~/.claude/settings.json`) | User-trusted; runs without workspace dialog | — |
| Project settings (`.claude/settings.json`) | Requires workspace trust dialog at first use | User can deny |
| Local project settings (`.claude/settings.local.json`) | Workspace trust (same as project) | User can deny |
| Plugin `hooks/hooks.json` | Plugin trust level | Plugin must be installed |
| Skill / subagent frontmatter | Workspace trust | Inherits project trust decision |
| `allowManagedHooksOnly` (enterprise) | Blocks all non-managed hooks | Admin-only |

**Design consequence:** trust is not a single boolean. A hook from `~/.claude/settings.json` runs even when the workspace itself is untrusted. Only `allowManagedHooksOnly` produces a hard all-or-nothing gate across all scopes.

The Python harness in this kit simplifies this to a single `workspace_trusted` flag for portability. Production deployments should map to the scope hierarchy above.

### Fail-closed exception handling

Wrap each hook invocation in `try`/`except`:

- A pre-hook that raises is treated as `(False, "exception")` — call is vetoed, exception logged, loop continues.
- A post-hook that raises is logged and silently swallowed — telemetry failures must not break the tool's user-visible result.

## End-of-session routine

The loop exits when one of these fires:

| Reason         | Trigger                                | What the harness must do |
|----------------|----------------------------------------|--------------------------|
| `done`         | Model returns a "task complete" signal | Append final summary event |
| `iteration_cap`| Iteration counter hits the cap         | Append `cap_hit` event with the last goal state |
| `user_abort`   | `KeyboardInterrupt`                    | Flush, append `aborted` event, exit non-zero |
| `error`        | Tool or hook raised uncaught           | Append `error` event with traceback |

In all four cases, the agent's responsibility is to update `progress.md` and `session-handoff.md` *before* the process exits, so the next session has a starting point. The harness should *not* auto-write these files — see [Context and memory](context-and-memory.md).

## Iteration cap and timeout discipline

- **Iteration cap**: configurable per session, default 10 (mock), 30 (live). Hard cap, no override at runtime.
- **Per-tool timeout**: 30s for `run_shell`, configurable per tool. Use `subprocess.run(..., timeout=N)` and let `TimeoutExpired` propagate as a tool failure.
- **Cumulative budget** (optional): wall-clock seconds for the whole session. Useful for CI where a runaway agent burns minutes.

The cap is the most important number in the harness. It is the only thing standing between a creative model and an infinite loop.

## Related references

- [Architecture principles](architecture-principles.md) — bounded-loop and durability invariants.
- [Tool registry and safety](tool-registry-and-safety.md) — what hooks gate and why.
- [Nine components](nine-components.md) — `harness.py` and `hooks.py` are components 1 and 8.
