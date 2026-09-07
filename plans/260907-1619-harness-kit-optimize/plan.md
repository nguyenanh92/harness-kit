---
title: "Harness Kit — Bug Fixes & Optimization"
description: "Fix critical template bugs, close test coverage gaps, harden CI, and resolve repo hygiene issues found in the 2026-09-07 audit."
status: completed
priority: P1
effort: "4-5h total"
tags: ["harness-kit", "bugfix", "testing", "ci"]
created: 2026-09-07
---

# Harness Kit — Bug Fixes & Optimization

## Overview

Four-phase remediation of issues found during the 2026-09-07 evaluation (B+/82).
Phases are ordered by impact: security/correctness first, then test coverage,
then CI hardening, then housekeeping.

## Goals

| # | Goal | Priority |
|---|------|----------|
| 1 | Fix two template bugs that contradict the kit's own gotchas | P1 |
| 2 | Add live harness loop tests — biggest coverage gap | P1 |
| 3 | Make CI honest about the repo's harness score | P2 |
| 4 | Clean up git hygiene + add-in-demo gitignore + AGENTS.md | P2 |

## Acceptance Criteria

- [ ] `classify_command("rm somefile")` returns `WORKSPACE_WRITE` (not `READ_ONLY`)
- [ ] `prompt_assembly.py` ancestor walk stops at `.git` boundary
- [ ] `test_skill.py` covers harness loop: mock adapter, compaction trigger, hook block
- [ ] CI `validate_harness.py` step enforces `--min-score 60`, not `--min-score 0`
- [ ] `js/main.js` deletion committed; `add-in-demo/node_modules` in `.gitignore`
- [ ] `AGENTS.md` at repo root (or `CLAUDE.md`) with minimal governance
- [ ] `test_skill.py` 10/10 → N/10 still green (no regressions)

## Phases

| Phase | Title | Status | Effort |
|-------|-------|--------|--------|
| 01 | Template Bug Fixes | pending | 1h |
| 02 | Harness Loop Test Coverage | pending | 1.5h |
| 03 | CI Hardening | pending | 45m |
| 04 | Repo Hygiene | pending | 30m |

## Dependencies

None. Phases 01–04 are independent; 03 depends on 01+02 being correct first
(CI must validate the fixes), so recommended execution order: 01 → 02 → 03 → 04.

## Risk

- `classify_command` fix may be too broad — overly aggressive classification
  blocks legitimate read commands. Mitigation: keep a word-boundary approach
  and test both `rm -rf /` and `rm somefile` and `grep pattern file`.
- Ancestor-walk change could break projects where the workspace IS the git root.
  Mitigation: stop at `.git` OR at the workspace root, whichever is reached first.
