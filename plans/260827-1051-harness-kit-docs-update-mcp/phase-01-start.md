---
phase: 1
title: "Fix factual errors in reference docs"
status: pending
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Fix factual errors in reference docs

## Overview

Correct 4 claims that contradict how Claude Code actually works. These are quick targeted edits — no new files, no structural changes.

## Requirements

- Functional: each corrected claim must match the current Anthropic documentation
- Non-functional: edits must be surgical; do not restructure surrounding content

## Architecture

Four independent file edits. Each is self-contained.

## Related Code Files

- Modify: `skills/references/nine-components.md`
- Modify: `skills/references/lifecycle-and-hooks.md`
- Modify: `skills/references/tool-registry-and-safety.md`
- Modify: `skills/references/context-and-memory.md`

## Implementation Steps

### 1. `nine-components.md` — Sub-agent nesting depth

**Current (wrong):** "Fork Children Must Not Fork" / single-level restriction applies to all sub-agents

**Fix:**
- Distinguish **forks** (inherit full history, share prompt cache, cannot spawn further → single-level) from **regular sub-agents** (can nest up to 3 levels via `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, default 3, concurrent limit 20)
- Add `SendMessage` tool as the peer-to-peer subagent communication mechanism
- Update the sub-agent component description to reflect both fork and subagent spawn paths

### 2. `lifecycle-and-hooks.md` — Hook trust model

**Current (wrong):** "All-or-nothing" — single `workspace_trusted` flag

**Fix:**
- Replace all-or-nothing model with 7-scope trust hierarchy:
  1. Managed policy settings (admin-controlled, always runs)
  2. `~/.claude/settings.json` (user-trusted)
  3. `.claude/settings.json` (workspace trust dialog)
  4. `.claude/settings.local.json` (workspace trust)
  5. Plugin `hooks/hooks.json` (plugin trust)
  6. Skill/subagent frontmatter (workspace trust)
  7. `allowManagedHooksOnly` enterprise flag (blocks all non-managed hooks)
- Add 5 hook types (not just pre/post): `command`, `http`, `mcp_tool`, `prompt`, `agent`
- Add exit-code contract: exit `2` = block; exit `0` = proceed; exit `1/3-N` = non-blocking error
- Add note: hooks run outside the context window (zero token cost)
- Add `PreCompact` event and `SubagentStop` / `FileChanged` / `InstructionsLoaded` events

### 3. `tool-registry-and-safety.md` — Permission model

**Current (wrong):** 3-tier READ_ONLY / WORKSPACE_WRITE / FULL_ACCESS only

**Fix:**
- Keep the 3-tier classifier as the per-call classification mechanism (it remains valid)
- Add the 6 permission **modes** that sit above the classifier:
  - `default` — prompts for sensitive actions
  - `acceptEdits` — auto-approves file edits, prompts for shell
  - `plan` — read-only, no writes or shell
  - `dontAsk` — denies instead of prompting
  - `auto` — model classifier decides
  - `bypassPermissions` — full access with critical-path guardrails
- Add 6-step evaluation order per tool call: Hooks → Deny rules → Ask rules → Permission mode → Allow rules → `canUseTool` callback
- Add scoped pattern examples: `Bash(rm *)`, `Edit(//secrets/**)`, `mcp__github__get_*`
- Add: critical paths (`rm`/`rmdir` on system dirs) blocked in ALL modes including `bypassPermissions`

### 4. `context-and-memory.md` — Compaction threshold

**Current (wrong):** 80% of max_tokens

**Fix:**
- Update threshold to **~95%** (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`)
- For a 200K window: trigger at ~190K tokens, not ~160K
- Reserved response buffer: ~33K tokens (16.5% of 200K)
- Note that `PreCompact` hook fires before compaction (allow transcript archiving)
- Note that CLAUDE.md is re-injected from disk after compaction (not lost)
- Add `compact_boundary` event emitted in SDK stream after compaction

## Success Criteria

- [x] `nine-components.md`: fork vs. subagent distinction clear; 3-level depth documented; `SendMessage` mentioned
- [x] `lifecycle-and-hooks.md`: 7-scope trust table present; 5 hook types listed; exit-code contract documented; `PreCompact` event noted
- [x] `tool-registry-and-safety.md`: 6 permission modes table added; 6-step evaluation order documented; scoped patterns shown
- [x] `context-and-memory.md`: compaction threshold is ~95%; `PreCompact` hook noted; CLAUDE.md re-injection noted

## Risk Assessment

Low risk — these are corrections to prose descriptions, not code changes. The classifier logic in `tool-registry-and-safety.md` is not removed, only augmented with the modes layer above it.
