# Context and Memory

Load when the agent is running out of context, when sessions need to survive a crash, or when prefix caching is dropping unexpectedly.

## Two distinct problems

| Problem        | Symptom                                       | Owned by                |
|----------------|-----------------------------------------------|-------------------------|
| Token budget   | LLM call rejects with "context too long"      | `context_manager.py`    |
| Durability     | Session crash loses all prior tool results    | `persistence.py`        |

These often get conflated. Compaction throws away tokens to keep the *current* call working. Persistence keeps every event on disk to make the *next* session resumable. You need both.

## Compaction

The default threshold in `ContextManager` is **80% of `max_tokens`**. When the running estimate crosses that line:

1. Keep the system prompt verbatim — it lives at the cache prefix and must not change.
2. Keep the last N=4 user/assistant/tool turns verbatim — recency matters more than mid-session detail.
3. Replace the middle band with a single synthesized `system` message summarizing what happened (decisions, files touched, errors hit, current goal).

Token estimation is intentionally cheap: `len(text) // 4`. Anything fancier requires a tokenizer dependency and burns CPU on every turn. Off by a few percent is fine; the threshold is a soft signal, not an absolute limit.

**Do not compact below the floor.** Always preserve the system prompt and the last turn even if you have to exceed the threshold; a compacted context that no longer makes sense to the model is worse than a near-full one.

## Prefix caching

Anthropic and OpenAI cache the *prefix* of identical messages between calls. The harness only benefits if the first N tokens are byte-identical across iterations.

**Rules that keep the cache warm:**
- The system prompt is assembled once per session and only *appended* to. Never rewrite earlier sections.
- Project guidelines (from `CLAUDE.md` / `AGENTS.md`) are appended after the base system prompt, *not* inserted at the top.
- Compaction never edits the prefix. Summaries go into a new `system` message *after* the original prompt.
- Timestamps in the prompt break the cache — keep timestamps inside `data` payloads in the log, not in the system text.

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

`progress.md` and `session-handoff.md` are the *cross-session* memory. They are not in the prompt automatically — the agent reads them at startup (see `AGENTS.md`'s Startup Workflow). This is on purpose:

- The JSONL log is for *intra-session* replay.
- The Markdown files are for *human-curated* hand-off. They survive log rotation, summarize at a higher level, and remain useful even after months.

Do not auto-write `progress.md` from the loop. The agent must compose it deliberately at end-of-session — the act of writing it forces a re-grounding that an auto-generated summary skips.

## Related references

- [Architecture principles](architecture-principles.md) — why JSONL is the durability story.
- [Nine components](nine-components.md) — modules involved (2, 6, 7).
- [Gotchas](gotchas.md) — prefix-cache invalidation traps, silent flush failures.
