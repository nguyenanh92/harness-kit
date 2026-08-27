---
phase: 4
title: "Gotchas + README sync"
status: pending
priority: P2
effort: "2h"
dependencies: [1, 2, 3]
---

# Phase 4: Gotchas + README sync

## Overview

Add newly discovered failure modes to `gotchas.md`, update `README.md` to reflect corrected claims, and sync `README-VI.md` with any English claim changes.

## Requirements

- Functional: gotchas must match current Claude Code behavior; README summary must not contradict the updated reference docs
- Non-functional: README changes must be minimal — only where claims were factually wrong

## Architecture

No architectural changes. This phase is documentation-only cleanup after the substantive edits in Phases 1–3.

## Related Code Files

- Modify: `skills/references/gotchas.md`
- Modify: `README.md`
- Modify: `README-VI.md`

## Implementation Steps

### 1. Add new gotchas to `skills/references/gotchas.md`

Add these entries (number continuing from existing 16):

**#17 — Timestamp in MCP tool schema busts prefix cache**
MCP tool schemas are part of the stable prefix. If the MCP server injects a timestamp or request ID into schema descriptions, the prefix cache is invalidated on every iteration. Keep MCP tool schema descriptions static.

**#18 — Subagent nesting depth vs fork depth confused**
The single-level fork restriction applies to **forks** only (sub-processes that inherit full history). Regular sub-agents can nest 3 levels deep. Applying single-level restriction to all subagents unnecessarily limits parallelism.

**#19 — Hook exit code 1 is non-blocking**
Only exit code `2` blocks a tool call. Exit code `1` is treated as a non-blocking error (logged, execution continues). Using exit 1 to try to veto a tool silently fails.

**#20 — compaction threshold misconfigured to 80% causes premature compaction**
The default threshold is ~95% (not 80%). Setting `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=80` causes compaction at ~160K/200K tokens, losing 30K tokens of usable context unnecessarily.

**#21 — Auto memory MEMORY.md over 200 lines silently truncated**
Only the first 200 lines of MEMORY.md are loaded at session start. Entries past line 200 are invisible without explicit loading. Keep MEMORY.md as a concise index; put details in per-entry topic files.

**#22 — MCP tool list assumed static at session start**
MCP servers can send `notifications/tools/list_changed` at any time. A harness that caches the tool list at startup will miss new tools added mid-session by a server.

### 2. Update `README.md`

Scan the Gotchas section (currently 6 gotchas listed):

- Gotcha 4 "All-or-Nothing Hook Trust" — update to note the 7-scope model exists; remove "all-or-nothing" framing as a fixed rule
- Gotcha 5 (if "Sub-Agent Recursion: Fork Children Must Not Fork") — update to clarify fork vs. subagent distinction

Check the 9-component descriptions in README for any that echo the wrong sub-agent or hook claim; fix inline.

Do NOT rewrite sections that are conceptually correct (formula, loop, persistence, permissions classifier).

### 3. Sync `README-VI.md`

Apply identical changes to the Vietnamese counterpart. README-VI.md is a translation of README.md — wherever English was fixed, update the Vietnamese text to match.

Use the same sentence structure as surrounding Vietnamese text; do not introduce new vocabulary.

## Success Criteria

- [x] `gotchas.md` has 6 new entries (#17–#22) with actionable descriptions
- [x] `README.md` gotchas section updated for hook trust and sub-agent fork framing
- [x] `README.md` has no claim that contradicts the Phase 1–3 fixes
- [x] `README-VI.md` is in sync with all English changes
- [x] No broken anchor links (cross-check if README links to reference docs by section name)

## Risk Assessment

Low for gotchas (additive). Medium for README — the Vietnamese translation must preserve tone and technical accuracy. If unsure about a Vietnamese phrasing, preserve the existing structure and only change the specific claim.
