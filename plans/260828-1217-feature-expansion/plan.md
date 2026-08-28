---
title: "Outlook AI Co-Pilot — Feature Expansion"
description: "Add Translate tab, Custom Reply Context, and Tone Analysis to the add-in"
status: pending
priority: P1
effort: "5-6h total"
tags: ["outlook", "add-in", "ai", "react"]
created: 2026-08-28
---

# Outlook AI Co-Pilot — Feature Expansion

## Overview

Build three high-value additions on top of the current add-in (F-001…F-008 done):
a **Translate tab** for quick Vietnamese↔English conversion, a **Custom Reply Context**
field so users can steer AI replies with natural instructions, and a **Tone Badge**
that shows the sender's detected tone inside the Summary tab.

All phases are self-contained and do not require manifest changes. Each phase
touches the frontend only (React + TypeScript + Tailwind) and the existing AI
client layer (`claude-client.ts` / `deepseek-client.ts`).

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Translate email body Vietnamese↔English with one click | P1 |
| 2 | Let user add custom context/instructions before AI generates replies | P1 |
| 3 | Show sender tone badge (Urgent / Formal / Friendly / Neutral) in Summary | P2 |

## Phases

| # | Phase | Status | Effort |
|---|-------|--------|--------|
| 1 | [Translate Tab](./phase-01-start.md) | Pending | ~2h |
| 2 | [Custom Reply Context](./phase-02-custom-reply-context.md) | Pending | ~2h |
| 3 | [Tone Analysis Badge](./phase-03-tone-analysis.md) | Pending | ~1.5h |

## Success Criteria

- [ ] Translate tab appears as the 4th tab; correctly translates Vietnamese↔English
- [ ] Reply tab has an Instructions textarea; regenerating with context changes the output
- [ ] Summary tab shows a tone badge derived from the AI response
- [ ] `npm run build` (tsc -b && vite build) passes with 0 errors after each phase
- [ ] No regressions in existing Summary / Reply / Settings tabs

## Affected Files

```
src/app.tsx                          — add "translate" Tab type, route tab
src/components/tab-bar.tsx           — add globe icon + Translate tab
src/components/translate-tab.tsx     — NEW
src/components/reply-tab.tsx         — add Instructions textarea + regenerate
src/components/summary-tab.tsx       — add tone badge rendering
src/api/claude-client.ts             — add translateEmail(), extend SummaryResult
src/api/deepseek-client.ts           — add deepseekTranslate(), extend deepseekSummarize
add-in-demo/feature_list.json        — add F-009, F-010, F-011
```

<!-- slug: feature-expansion -->
