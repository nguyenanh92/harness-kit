---
title: "harness-kit docs update + MCP optional integration"
description: "Fix 4 factually wrong claims in current docs, add MCP as an optional layer, and document missing concepts (Auto Memory, Prompt Caching)."
status: completed
priority: P1
effort: "1.5d"
tags: [docs, mcp, harness, architecture]
created: 2026-08-27
---

# harness-kit docs update + MCP optional integration

## Overview

The current harness-kit documentation has 4 factually incorrect claims compared to how Claude Code actually works in 2025-2026, and is missing MCP entirely — now the dominant tool federation mechanism. This plan fixes the wrong claims, adds MCP as an optional harness layer (not required), and documents Auto Memory and Prompt Caching which are now load-bearing architectural concepts.

**Research basis:** `plans/reports/researcher-260827-1043-harness-architecture-audit.md`

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Fix 4 factually wrong claims across reference docs | P1 |
| 2 | Add MCP as an optional integration layer (not a hard requirement) | P1 |
| 3 | Document Auto Memory and Prompt Caching concepts | P2 |
| 4 | Update gotchas with newly discovered failure modes | P2 |
| 5 | Keep zero-external-deps as the default/core invariant; MCP is explicitly opt-in | P1 |

## Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | [Phase 1: Fix factual errors](./phase-01-start.md) | Pending |
| 2 | [Phase 2: MCP optional integration doc](./phase-02-mcp-optional.md) | Pending |
| 3 | [Phase 3: Auto Memory + Prompt Caching](./phase-03-auto-memory-prompt-caching.md) | Pending |
| 4 | [Phase 4: Gotchas + README sync](./phase-04-gotchas-readme-sync.md) | Pending |

## Files in Scope

**Modify:**
- `skills/references/nine-components.md`
- `skills/references/tool-registry-and-safety.md`
- `skills/references/context-and-memory.md`
- `skills/references/lifecycle-and-hooks.md`
- `skills/references/architecture-principles.md`
- `skills/references/gotchas.md`
- `README.md`
- `README-VI.md`
- `skills/SKILL.md`

**Create:**
- `skills/references/mcp-integration.md` (new — optional MCP layer guide)

**Do NOT touch:**
- `skills/scripts/` (no code changes in this plan)
- `skills/templates/` (governance templates unchanged)
- `demo/` (demo has its own reference set; update only if explicit)

## Success Criteria

- [ ] Sub-agent nesting depth documented correctly (3 levels for subagents; single-level for forks)
- [ ] Hook trust model updated to 7-scope (not all-or-nothing)
- [ ] Permission model updated to 6 modes + 6-step evaluation chain
- [ ] Compaction threshold corrected to ~95% with `PreCompact` hook noted
- [ ] `mcp-integration.md` exists and clearly marks MCP as optional
- [ ] Auto Memory and Prompt Caching have dedicated sections in `context-and-memory.md`
- [ ] `architecture-principles.md` explicitly states MCP is opt-in (zero-deps is default)
- [ ] No broken cross-references between docs
- [ ] Vietnamese README updated if English claims changed

<!-- slug: harness-kit-docs-update-mcp -->
