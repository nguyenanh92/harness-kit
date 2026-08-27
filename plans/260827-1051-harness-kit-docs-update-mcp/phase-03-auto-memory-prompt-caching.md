---
phase: 3
title: "Auto Memory + Prompt Caching concepts"
status: pending
priority: P2
effort: "3h"
dependencies: [1]
---

# Phase 3: Auto Memory + Prompt Caching concepts

## Overview

Document two architectural concepts that are now load-bearing in production harnesses but are entirely absent from the current docs: Auto Memory (structured typed memory layer above JSONL) and Prompt Caching (automatic prefix caching with major cost/latency impact).

## Requirements

- Functional: a developer reading `context-and-memory.md` must understand both layers after this change
- Non-functional: do not bloat the file — add sections, not separate documents

## Architecture

### Auto Memory

Two-tier memory model (replaces single JSONL description):

```
Tier 1 (INTRA-SESSION): .harness/<session>.jsonl  ← append-only, crash recovery
Tier 2 (CROSS-SESSION): memory/ directory          ← structured, typed, queryable
    MEMORY.md (index, first 200 lines / 25KB loaded at session start)
    per-entry topic files (loaded on demand by relevance)
    4 typed categories: user | feedback | project | reference
```

### Prompt Caching

```
[Static prefix]          ← system prompt + CLAUDE.md + tool schemas
      ↑ cached automatically after first call
[Dynamic suffix]         ← task-specific messages, tool results
      ↑ never cached (changes every iteration)
```

Cache invalidation triggers: ANY mutation to the static prefix resets the cache.

## Related Code Files

- Modify: `skills/references/context-and-memory.md`

## Implementation Steps

### 1. Add "Auto Memory" section to `context-and-memory.md`

Add after the existing JSONL/persistence section:

**Content:**
- The memory/ directory as a second persistence tier (structured, typed)
- MEMORY.md as an index (first 200 lines loaded every session)
- 4 typed categories: `user` (role, preferences), `feedback` (DO/DON'T rules), `project` (goals, deadlines), `reference` (where things live in external systems)
- Loading strategy: index always loaded; topic files loaded on demand
- Agent writes memory deliberately (not auto-written by harness loop) — same pattern as progress.md
- Relation to JSONL: JSONL is intra-session replay; memory/ is cross-session knowledge
- Subagents can have own memory scope (isolated from parent)

**Two-step save protocol:**
1. Write entry file with frontmatter (name, description, type)
2. Add pointer to MEMORY.md index (one line, under ~150 chars)

**What NOT to save in memory** (important for governance docs):
- Code patterns, file paths, architecture — derivable from code
- Git history — use `git log`
- Debugging solutions — in the code and commit message
- Ephemeral task details

### 2. Add "Prompt Caching" section to `context-and-memory.md`

Add in or after the existing "Prefix Caching Rules" section (currently describes assembly order but doesn't explain caching cost impact):

**Content:**
- Automatic for stable prefixes: system prompt, CLAUDE.md, tool schemas
- Cache TTL: 5 minutes (re-warmed on each hit within TTL)
- Cache invalidation: any mutation to prefix resets it — timestamp in prompt = cache bust every call
- Cost/latency impact: cache hits dramatically reduce cost; this is why the "no timestamps in prompt" gotcha exists
- MCP tool schemas: deferred by default ("tool search") — only names load at session start, full schemas on demand. This is a cache optimization, not a limitation.
- How to design for cache: keep system prompt + CLAUDE.md + tool schemas stable; put task-specific content in user messages

### 3. Update the "Two Distinct Problems" table

Current table has: Token budget / Durability

Update to Three Distinct Problems:

| Problem | Symptom | Owner |
|---------|---------|-------|
| Token budget | LLM rejects "context too long" | context_manager.py |
| Durability | Session crash loses progress | persistence.py + memory/ |
| Cache efficiency | High cost / slow responses per call | prompt_assembly.py (prefix stability) |

## Success Criteria

- [x] `context-and-memory.md` has an "Auto Memory" section with two-tier model, 4 typed categories, and two-step save protocol
- [x] `context-and-memory.md` has a "Prompt Caching" section explaining automatic caching, TTL, invalidation triggers, and design guidance
- [x] "Two Distinct Problems" table updated to Three
- [x] No content contradicts Phase 1 fixes (compaction threshold and PreCompact hook already corrected there)
- [x] File stays under 800 lines (docs.maxLoc constraint from project rules)

## Risk Assessment

Low — additive changes only. Risk: file length. Mitigate by writing concisely and cutting filler from existing content rather than just appending.
