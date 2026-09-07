# Progress

## Current State

Active feature: none — all features done (F-001, F-002, F-003)

## What I Did

- F-001: Fixed `classify_command` to route `rm somefile` → WORKSPACE_WRITE;
  `rm -rf` / `rm -r` → FULL_ACCESS. Added `mv`, `cp`, `truncate` to WORKSPACE_WRITE tier.
- F-001: Fixed `prompt_assembly.find_guidelines_file` to stop at `.git` boundary
  (Gotcha #5) instead of walking to filesystem root.
- F-002: Added 5 integration tests to `test_skill.py` (15/15 passing):
  `test_classify_command_table`, `test_prompt_assembly_boundary`,
  `test_harness_mock_loop`, `test_context_compaction_triggers`,
  `test_hook_veto_blocks_execution`.
- F-003 (in progress): Hardened CI — fixed `--harness-dir skills/templates`,
  raised `--min-score`, added artifact upload. Added `AGENTS.md`, `feature_list.json`,
  `progress.md`, `session-handoff.md`. Fixed `persistence.py` silent JSONL skip.

## Verification Evidence

```
py test_skill.py
OK  15/15 passed
```

## Recommended Next Step

Complete F-003: commit `js/main.js` deletion, run final score check, commit all changes.

## Last Updated

2026-09-07
