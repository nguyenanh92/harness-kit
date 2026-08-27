# Gotchas

Non-obvious failure modes specific to a standard-library Python harness. Numbered so other references can link by ID; do not renumber on edits — append.

## 1. Silent JSONL truncation on crash

`f.write(line)` without `f.flush()` leaves the last few events in the OS buffer. A SIGKILL between write and flush yields a JSONL file that *looks* fine but is missing the events you most need to debug. Fix: flush on every event, and pair with `os.fsync(f.fileno())` if you cannot tolerate kernel-level loss either.

## 2. Prefix-cache invalidation by timestamp in the prompt

If your system prompt contains the session's start time (or any per-run identifier), every iteration is a cache miss. Move all such values into the JSONL `data` payload. Keep the prompt byte-identical across iterations.

## 3. `rm` matches `rm -rf`

A naive substring classifier that lists `"rm -rf"` *after* `"rm "` will silently route `rm -rf /` to `WORKSPACE_WRITE`. Always check the more dangerous patterns first, and always normalize with `.strip().lower()` before comparison.

## 4. Hook timeout traps the tool

Pre-tool hooks share the tool's timeout budget. A hook that spins for 25s leaves the actual tool 5s to complete. Either give hooks their own (small) timeout, or document the shared budget so users do not write slow hooks.

## 5. Sub-agent ancestor walk leaks parent guidelines

`PromptAssembler.find_guidelines_file` walks up to the filesystem root by default. In a nested project (`~/work/main-repo/sub-project/`), the sub-agent may inadvertently load the main repo's `CLAUDE.md`. Stop at the workspace's `.git` directory or at the project root.

## 6. Compaction that drops the last turn

A summarizer that compacts everything except the system prompt loses the model's most recent reasoning. Always preserve at least the last N=4 turns *verbatim*; summarize only the middle.

## 7. Off-by-one in iteration cap

`while iteration <= max_iterations` and `while iteration < max_iterations` differ by exactly one expensive LLM call. Pick one convention and stick to it. The Python harness uses strict `<` and increments at the *top* of the loop.

## 8. `subprocess.run(shell=True)` and arg injection

`run_shell` shells out with `shell=True` to allow pipes and redirection. That makes the tool argument-injection-prone: a model that calls `run_shell` with `"ls; rm -rf $HOME"` will execute both commands. The permission classifier catches the obvious cases; the harness must still treat all shell calls as untrusted input.

## 9. Hook trust decided per file

If you allow per-hook trust decisions within a scope ("this hook looks safe, that one doesn't"), the attack model becomes "ship a safe-looking hook that calls back to a malicious one." Within any given trust scope, trust must be all-or-nothing — do not cherry-pick hooks. See [Lifecycle and hooks](lifecycle-and-hooks.md) for the full 7-scope hierarchy.

## 10. Replay re-executes side effects

A replay implementation that re-runs `tool_call` events to "reconstruct state" will, the second time, re-`rm` files, re-`git commit`, and re-`curl` endpoints. Replay reconstructs *the message history*, not the world. Tools are not pure functions.

## 11. Single shared log between forked processes

If a parent and sub-agent write to the same `.jsonl`, interleaved lines corrupt the JSON-per-line invariant under any non-trivial concurrency. Each agent gets its own log file under `.harness/`. Cross-reference by parent session id in the child's first event.

## 12. `validate_harness.py` keyword stuffing

The scorer matches case-insensitive substrings (with word boundaries). A file that lists every keyword *can* score 100/100 without being a usable harness. The score is structural; pair it with real before/after agent sessions on representative tasks.

## 13. `pip install` inside the harness

The harness must not install packages at runtime. A `pip install` event during a session means the harness is no longer reproducible and the cached prefix is now lying about what is importable. Put package-installation tools behind explicit `FULL_ACCESS` and treat them as session boundaries — flush logs, exit, restart.

## 14. `os.path` vs `pathlib` mixing

Mixing `os.path.join(...)` with `pathlib.Path(...)` on Windows yields `C:/repo\harness/file.py`-style frankenpaths that *work* but break exact-match logic (cache keys, log paths, log indexes). Pick `pathlib` everywhere in new code and resolve with `.resolve()` at module boundaries.

## 15. `init.sh` may not be executable after scaffolding on Windows

Scaffolding from Windows writes `init.sh` without an executable bit (NTFS has no concept of one). When a teammate clones the repo on Linux/macOS, `./init.sh` fails with permission denied. Fix at clone time:

```bash
chmod +x init.sh
git update-index --chmod=+x init.sh && git commit -m "make init.sh executable"
```

The Python scaffolder calls `make_executable` after writing, but the effect is a no-op on Windows. Commit the executable bit explicitly via Git.

## 16. Definition of Done is a documentation file, not a check

`AGENTS.md` says "tests pass." That is enforced by *the agent*, not by the harness. If you need a hard gate, wire it into `init.sh` so a non-zero exit code blocks the agent from declaring done. The validation score will tell you the *file says* tests must pass; only the verification script can tell you *whether* they did.

## 17. MCP tool schema contains a timestamp — cache busts every call

MCP tool schemas are part of the stable prefix. If the MCP server injects a per-request timestamp or session ID into a schema description field, the prefix cache is invalidated on every iteration. Keep MCP tool schema descriptions strictly static; put any dynamic metadata inside the tool's return payload.

## 18. Subagent nesting depth vs. fork depth confused

The single-level restriction applies to **forks** only — sub-processes that inherit the full conversation history. Regular subagents (fresh context, own JSONL log) can nest up to 3 levels. Applying the single-level constraint to all child spawns unnecessarily limits parallelism and is architecturally incorrect.

## 19. Hook exit code 1 is non-blocking

Only exit code `2` vetoes a tool call. Exit code `1` is a non-blocking error: it is logged and execution continues. Writing a hook that exits 1 to try to block a call silently fails — the call proceeds. Use exit code `2` to veto.

## 20. Compaction threshold misconfigured to 80% on a 200K-context model

A threshold of 80% triggers compaction at ~160K tokens on a 200K-context model, discarding ~30K tokens of usable context unnecessarily. Calibrate the threshold to the model's actual window: ~95% (~190K tokens for 200K window) with a ~33K response reserve. Override via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`.

## 21. Auto memory MEMORY.md over 200 lines silently truncated

Only the first 200 lines of `MEMORY.md` are loaded at session start. Entries past line 200 are invisible to the agent without an explicit read call. Keep `MEMORY.md` as a concise one-line-per-entry pointer index; put content in per-entry topic files.

## 22. MCP tool list assumed static at session start

MCP servers can send `notifications/tools/list_changed` at any time during a session. A harness that fetches the tool list once at startup will miss tools added (or removed) mid-session. Subscribe to the notification and re-fetch on change.

## Related references

- [Architecture principles](architecture-principles.md) — invariants these gotchas violate.
- [Tool registry and safety](tool-registry-and-safety.md) — classifier and trust details.
- [Context and memory](context-and-memory.md) — cache and JSONL pitfalls.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — bootstrap and end-of-session edges.
- [MCP integration](mcp-integration.md) — MCP-specific gotchas (#17, #22).
