---
title: "Harness Kit — UX Fixes"
description: "Fix broken hk.py audit, missing first-use guide, undocumented install flags, and init template confusion."
status: completed
priority: P1
effort: "4-5h total"
tags: ["harness-kit", "ux", "install", "hk.py"]
created: 2026-09-07
---

# Harness Kit — UX Fixes

## Context

UX audit (2026-09-07) identified 4 issues that hurt new users before they get
any value from the kit. Ordered by impact.

## Acceptance Criteria

- [ ] `py hk.py audit` works immediately after `install.sh | sh` — no extra steps
- [ ] `py hk.py audit --html report.html` produces a valid HTML file in-project
- [ ] After scaffold, terminal prints 3 concrete next-step commands (not just "Edit AGENTS.md")
- [ ] `hk.py status` with empty `feature_list` prompts user with a first step instead of crashing
- [ ] README documents `--full`, `--agent-file`, and pipe flag-passing for both platforms
- [ ] All 15 existing `test_skill.py` tests still pass

## Phases

| Phase | Title | Status | Effort | Impact |
|-------|-------|--------|--------|--------|
| 01 | Inline scorer into `hk.py` | completed | 2h | Critical — audit broken |
| 02 | Post-install first-use guide | completed | 1h | High — onboarding gap |
| 03 | README install documentation | completed | 45m | Medium — discoverability |

## Dependencies

No external dependencies between phases. Recommended order: 01 → 02 → 03.
Phase 01 is the only blocker for users finding value; 02 and 03 can be done in parallel.

## Non-Goals

- Rewrite `hk.py` architecture
- Change the scoring algorithm (use same 5-subsystem logic as `harness_utils.py`)
- Modify `init.sh`/`init.ps1` logic (templates handle missing tests/ gracefully already)
- Add new hk.py commands
