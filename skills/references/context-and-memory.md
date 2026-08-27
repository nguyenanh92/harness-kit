# Context and Memory

Load when the agent is running out of context, when sessions need to survive a crash, or when prefix caching is dropping unexpectedly.

## Three distinct problems

| Problem          | Symptom                                        | Owned by                         |
|------------------|------------------------------------------------|----------------------------------|
| Token budget     | LLM call rejects with "context too long"       | `context_manager.py`             |
| Durability       | Session crash loses all prior tool results     | `persistence.py` + `memory/`     |
| Cache efficiency | High cost / slow responses per call            | `prompt_assembly.py` (prefix stability) |

These are often conflated. Compaction throws away tokens to keep the *current* call working. Persistence keeps every event on disk to make the *next* session resumable. Cache efficiency keeps per-call cost low by keeping the stable prefix byte-identical across iterations. You need all three.

## Compaction

The effective threshold is **~95% of `max_tokens`** (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`). For a 200K-token context window, compaction triggers at ~190K tokens. A reserved response buffer of ~33K tokens (16.5%) ensures the model always has room to reply.

> The Python harness in this kit ships with 80% as a starting point. Before deploying against a live model, align it to ~95% of the target model's actual window (e.g. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=95` for a 200K model). Leaving it at 80% discards ~30K usable tokens per session — see [Gotchas](gotchas.md) #20.

When the running estimate crosses the threshold:

1. Keep the system prompt verbatim — it lives at the cache prefix and must not change.
2. Keep the last N=4 user/assistant/tool turns verbatim — recency matters more than mid-session detail.
3. Replace the middle band with a single synthesized `system` message summarizing what happened (decisions, files touched, errors hit, current goal).
4. **Re-inject `CLAUDE.md` / `AGENTS.md` from disk** after compaction — the file may have changed since session start, and compaction clears the old injected copy.
5. Emit a `compact_boundary` event to the session log so downstream tools (Agent SDK stream consumers) can detect where compaction occurred.

**`PreCompact` hook.** Before step 3, fire the `PreCompact` lifecycle event. A registered handler can archive the full transcript to disk before the middle band is summarized away. This is the only reliable window to preserve verbatim tool results from earlier in the session.

Token estimation is intentionally cheap: `len(text) // 4`. Off by a few percent is fine; the threshold is a soft signal, not an absolute limit.

**Do not compact below the floor.** Always preserve the system prompt and the last turn even if you have to exceed the threshold; a compacted context that no longer makes sense to the model is worse than a near-full one.

## Prefix caching

Anthropic and OpenAI cache the *prefix* of identical messages between calls. Cache hits dramatically reduce per-call cost and latency — the stable prefix (system prompt + `CLAUDE.md` + tool schemas) can be 50–80% of the total token budget, and caching it cuts that cost to near zero after the first call. Cache TTL is 5 minutes; any call within that window re-warms the cache.

The harness only benefits if the first N tokens are byte-identical across iterations.

**Rules that keep the cache warm:**
- The system prompt is assembled once per session and only *appended* to. Never rewrite earlier sections.
- Project guidelines (from `CLAUDE.md` / `AGENTS.md`) are appended after the base system prompt, *not* inserted at the top.
- Compaction never edits the prefix. Summaries go into a new `system` message *after* the original prompt.
- Timestamps in the prompt break the cache — keep timestamps inside `data` payloads in the log, not in the system text.
- MCP tool schemas are part of the stable prefix. If an MCP server injects a timestamp or request ID into its schema descriptions, the cache busts on every call (see [Gotchas](gotchas.md) #17).

**Deferred tool schemas.** For large tool sets (e.g., MCP servers with many tools), load only tool *names* at session start and fetch full schemas on demand. This keeps the prefix shorter and reduces cold-start latency.

**The walk-ancestors rule.** `PromptAssembler.find_guidelines_file` walks up from `workspace_dir` until it finds a `CLAUDE.md` / `AGENTS.md`. Stop at the first match — do not concatenate guidelines from multiple ancestor directories. Stopping at the workspace's `.git` root prevents a parent-repo's instructions leaking into a nested project.

## Append-only persistence

Every event the loop produces lands in `.harness/<session>.jsonl` immediately. The shape:

```jsonl
{"ts": "2026-06-11T03:14:00Z", "iteration": 1, "type": "tool_call", "data": {"name": "read_file", "args": {"path": "src/x.py"}}}
{"ts": "2026-06-11T03:14:01Z", "iteration": 1, "type": "tool_result", "data": {"name": "read_file", "ok": true, "summary": "..."}}
{"ts": "2026-06-11T03:14:02Z", "iteration": 1, "type": "compaction", "data": {"kept_turns": 4, "summarized_chars": 18240}}
```

**Flush on every write.** `f.write(json.dumps(...) + "\n"); f.flush()`. The OS may buffer otherwise; a SIGKILL between buffer and disk loses the last few events — exactly the ones you most need to debug.

**Replay does not re-execute.** `replay_events()` rebuilds the message list and iteration counter; it does *not* re-run tool calls. If the agent needs the *current* state of a file, it calls `read_file` again. The log is for context, not for re-driving the world.

## Memory across sessions

Two tiers of cross-session memory serve different purposes:

### Tier 1 — Intra-session replay (JSONL)

`.harness/<session>.jsonl` is for replaying the current session after a crash. It is not loaded into future sessions automatically.

### Tier 2 — Structured cross-session memory (`memory/`)

A `memory/` directory at the project root provides typed, queryable knowledge that persists across sessions:

```
memory/
  MEMORY.md              ← index file; first 200 lines loaded at every session start
  user_role.md           ← example per-entry topic file
  feedback_testing.md
  project_goals.md
```

**Loading strategy:** Only `MEMORY.md` is loaded unconditionally (up to 200 lines / 25KB). Per-entry topic files are loaded on demand when their content is relevant. Keep `MEMORY.md` as a one-line-per-entry pointer index — not the content itself.

**Four typed categories:**

| Type | Stores |
|------|--------|
| `user` | Role, preferences, domain knowledge |
| `feedback` | DO/DON'T rules derived from corrections and confirmations |
| `project` | Goals, deadlines, active decisions |
| `reference` | Where to find things in external systems |

**Two-step save protocol.** Writing a memory entry is always two steps:
1. Write the entry to its own topic file with frontmatter (`name`, `description`, `type`).
2. Add a one-line pointer to `MEMORY.md` (file path + one-line hook, under ~150 chars).

The two-step requirement prevents `MEMORY.md` from becoming a monolith and keeps the index scannable.

**What NOT to store in memory:**
- Code patterns, file paths, or architecture — read the current source instead.
- Git history or who-changed-what — `git log` is authoritative.
- Debugging solutions or fix recipes — the fix is in the code; context belongs in the commit.
- Ephemeral task state from the current session.

**Subagent memory scope.** Each subagent may maintain its own `memory/` directory scoped to its workspace; parent and child memory are isolated by default.

### Human-curated handoff files

`progress.md` and `session-handoff.md` remain the primary mechanism for intentional, human-legible cross-session state. They are not loaded automatically — the agent reads them at startup (see `AGENTS.md`'s Startup Workflow).

Do not auto-write `progress.md` from the loop. The agent must compose it deliberately at end-of-session — the act of writing it forces a re-grounding that an auto-generated summary skips.

## Related references

- [Architecture principles](architecture-principles.md) — why JSONL is the durability story.
- [Nine components](nine-components.md) — modules involved (2, 6, 7).
- [Gotchas](gotchas.md) — prefix-cache invalidation traps, silent flush failures.
