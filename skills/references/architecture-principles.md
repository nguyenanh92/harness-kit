# Architecture Principles

Load when you are deciding what *not* to add to the harness. These three invariants are load-bearing; everything else is negotiable.

## 1. Zero external dependencies

The harness modules under `harness/` import only the Python standard library. No `requests`, no `langchain`, no `pydantic`.

**Why this is non-negotiable.** Sandboxes pull and audit dependencies at startup; every third-party package is a supply-chain surface, a version-drift risk, and a cold-start cost. The harness must work in any Python 3.8+ environment with nothing pre-installed.

**What you may use.**
- `subprocess`, `os`, `sys`, `signal` — process and shell.
- `json`, `pathlib`, `re`, `argparse` — config and parsing.
- `dataclasses`, `typing`, `enum` — typed data structures.
- `http.client`, `urllib`, `ssl` — network when an LLM call is needed (no `httpx`).

**Bright line.** If a feature requires a third-party package, push it behind a thin adapter in the *caller's* code, not into `harness/`.

**MCP carve-out (opt-in).** MCP integration is the one sanctioned exception. If you opt into MCP, the `mcp` Python SDK may be imported — but only in a dedicated adapter module (e.g., `harness_mcp/`), never inside `harness/`. The harness core remains dependency-free; the adapter is injected via the `model_turn` callable pattern. See [MCP integration](mcp-integration.md).

## 2. The while loop is the program

A harness is a bounded orchestrator of one loop. Every other module exists to feed it inputs or execute its decisions. The canonical step order:

```
+-------------------------------------------------------------+
|                        WHILE LOOP                           |
|  1. Assemble system prompt   (prompt_assembly.py)           |
|  2. Compact if near budget   (context_manager.py)           |
|  3. Call model               (live or mock)                 |
|  4. Parse tool call          (harness.py)                   |
|  5. Pre-tool hook            (hooks.py)                     |
|  6. Permission check         (tool_registry.py)             |
|  7. Execute tool             (tool_registry.py)             |
|  8. Post-tool hook           (hooks.py)                     |
|  9. Append event             (persistence.py)               |
| 10. Continue until done or iteration cap hit                |
+-------------------------------------------------------------+
```

**Mandatory constraints.**
- **Iteration cap** (default 10–30). No unbounded loops, ever.
- **Per-tool timeout** (default 30s on shell). Hung commands must be killable.
- **Single re-entry point.** Only `harness.py::Harness.run()` drives the loop. Sub-agents reuse the same loop with a restricted registry; they do not invent their own.

## 3. Durability via append-only JSONL

Every iteration appends one JSON object per event to `.harness/<session>.jsonl` and flushes immediately. The log *is* the session.

**Why append-only.**
- **Crash recovery.** A killed terminal or a power cut leaves a partial line at most; everything up to that line is intact.
- **Replay.** Resuming a session means re-reading the log top-to-bottom and reconstructing context, iteration count, and active feature. No external state store is required.
- **Concurrency safety.** Two readers never collide; if you ever fork the harness, each fork writes to its own log file (never a shared one).

**What an event must include.**
- `ts` — ISO-8601 timestamp.
- `type` — e.g., `tool_call`, `tool_result`, `compaction`, `hook_block`.
- `iteration` — current loop iteration.
- `data` — payload (tool name, args, exit code, summary, etc.).

If an event cannot be serialized to JSON, the harness must fail loudly — silent log corruption is the worst failure mode.

## Related references

- [Nine components](nine-components.md) — concrete mapping from these principles to modules.
- [Context and memory](context-and-memory.md) — what to compact and how to keep prefix caching intact.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — bootstrap stages and trust gates around the loop.
- [Gotchas](gotchas.md) — failure modes these principles exist to prevent.
