# Lifecycle and Hooks

Load when bootstrapping a session, when wiring hooks, or when designing the restart story.

## Bootstrap stages

A session starts cold; the harness should bring up trust *gradually*, not flip a single switch:

1. **Minimal.** Load `harness.py`, register built-in tools, open the JSONL log. No hooks, no sub-agents, no shell. The agent can read files only.
2. **Verification.** Run `./init.sh` / `./init.ps1` once. If it fails, refuse to advance — a broken workspace must not graduate to writes.
3. **Workspace write.** Enable `WORKSPACE_WRITE` shell commands. The agent can now scaffold and run tests.
4. **Trusted.** Enable hooks (if the workspace is trusted) and `FULL_ACCESS` shell with interactive approval. Sub-agents become spawnable.

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

## Hooks: pre- and post-tool

```python
PreHookFunc  = Callable[[str, dict], tuple[bool, Any]]   # (tool, args) -> (allow, args_or_reason)
PostHookFunc = Callable[[str, str], None]                # (tool, result) -> None
```

**Pre-tool hooks** can:
- Veto a call by returning `(False, "reason")`. The harness logs the veto and continues to the next iteration.
- Rewrite arguments by returning `(True, new_args)`. Useful for path normalization or secret redaction.
- Run synchronously only. Hooks share the tool's timeout; a hung hook fails the tool call.

**Post-tool hooks** are for telemetry, logging, and side-effect propagation. They cannot affect the tool's result — by the time they fire, the work is already done.

### Trust gate

The hook registry honors a single `workspace_trusted` flag. When false:

- `dispatch_pre_hooks` returns the unchanged arguments without invoking any registered pre-hook.
- `dispatch_post_hooks` is a no-op.

This is the **all-or-nothing** rule. Do not allow per-hook trust decisions; a single untrusted hook that looks safe is exactly the attack you cannot detect.

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
