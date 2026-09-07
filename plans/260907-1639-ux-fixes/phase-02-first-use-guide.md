---
phase: 2
title: "Post-install first-use guide"
status: pending
priority: P1
effort: "1h"
dependencies: []
---

# Phase 2: Post-install first-use guide

## Problem

After `install.sh | sh` succeeds, the user sees:
```
Done. Edit AGENTS.md (or CLAUDE.md) to customize rules for your project.
Supported tools: Claude Code, Cursor, Codex, Windsurf, and any AI that reads your instruction file.
```

This tells the user what to read, not what to do. A new user stares at 6 new
files and doesn't know the right first action. Two failure modes observed:
1. User opens AGENTS.md, reads it, then wonders "ok but what now?"
2. User runs `py hk.py status` — but `feature_list.json` has placeholder
   features (F-001 "Bootstrap harness") that confuse them

## Fix A — Scaffold output: 3-step guide

Change the final `print(...)` in `scaffold_harness.py` to emit concrete commands:

```
Done. Your agent harness is ready.

Next steps:
  1. Open your AI agent and say:
       "Read AGENTS.md and start working on F-001."

  2. Or manage features from the terminal:
       py hk.py status          # see active feature + queue
       py hk.py feature "My first task" --desc "What you want to build"
       py hk.py start F-003     # set it active

  3. When a feature is complete:
       py hk.py done            # runs init script + marks done
       py hk.py audit           # score your harness (0-100)

Works with Claude Code, Cursor, Codex, Windsurf — any AI that reads AGENTS.md.
```

Mirror this text in both `install.sh` and `install.ps1` (they currently duplicate the short message).

## Fix B — `hk.py status` with template feature_list

The scaffolded `feature_list.json` contains two placeholder features:
- F-001 "Bootstrap harness" (in_progress)
- F-002 "Wire verification" (pending)

These are intentional starters. But `hk.py status` currently prints them as-is,
which confuses users who haven't customized the list yet.

Add a one-line hint when the feature list contains only the default starter
entries (detected by name match):

```python
STARTER_IDS = {"F-001", "F-002"}

def _is_starter_list(features):
    ids = {f.get("id") for f in features}
    return ids == STARTER_IDS
```

When detected, append below the status output:
```
Tip: These are starter features. Replace them with your own:
  py hk.py feature "Your first task" --desc "What you want to build"
```

## Fix C — `hk.py status` when no feature is active

Currently, when no feature has `status: in_progress`, the CLI prints nothing
useful. Add:

```
No active feature. Start one:
  py hk.py start F-001       # or the ID of the feature you want
```

## Files

- **Modify:** `skills/scripts/scaffold_harness.py` — final print block (line ~109)
- **Modify:** `install.sh` — final echo block (lines 63–68)
- **Modify:** `install.ps1` — final Write-Host block (lines 65–71)
- **Modify:** `skills/templates/hk.py` — `cmd_status` function

## Implementation Steps

1. Update the `print(...)` at the end of `scaffold_harness.py::main()`.
2. Mirror the same text in `install.sh` (echo) and `install.ps1` (Write-Host).
3. Add `_is_starter_list` helper in `hk.py` and call it in `cmd_status`.
4. Add no-active-feature hint in `cmd_status`.
5. Run `py test_skill.py` — 15/15 must pass.

## Success Criteria

- [ ] Fresh scaffold prints 3-step guide with concrete commands
- [ ] `py hk.py status` on a fresh install shows starter-feature hint
- [ ] `py hk.py status` on an empty active-feature queue gives actionable output
- [ ] All 15 tests pass

## Risk Assessment

Low. These are print-statement changes and a helper function in `cmd_status`.
No logic changes, no new files, no breaking changes to the CLI interface.
