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

If you allow per-hook trust decisions ("this hook looks safe, that one doesn't"), the attack model becomes "ship a safe-looking hook that calls back to a malicious one." Trust must be all-or-nothing per workspace. Resist the temptation to be clever.

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

## Related references

- [Architecture principles](architecture-principles.md) — invariants these gotchas violate.
- [Tool registry and safety](tool-registry-and-safety.md) — classifier and trust details.
- [Context and memory](context-and-memory.md) — cache and JSONL pitfalls.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — bootstrap and end-of-session edges.
