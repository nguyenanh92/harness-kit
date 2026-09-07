---
phase: 2
title: "Harness Loop Test Coverage"
status: pending
priority: P1
effort: "1.5h"
dependencies: [1]
---

# Phase 2: Harness Loop Test Coverage

## Overview

The current `test_skill.py` covers scaffolding and validation scripts but has zero
coverage of the harness loop itself. The loop (`harness.py::Harness.run()`), context
compaction (`context_manager.py`), hook dispatch (`hooks.py`), and the `classify_command`
fix from Phase 1 are all untested. Add integration-style tests that run the mock loop
end-to-end and unit tests for the fixed classifier and ancestor walk.

## What to Test

### 2a — `classify_command` regression table

```
rm somefile           → WORKSPACE_WRITE
rm -rf /tmp           → FULL_ACCESS
rm -r dir             → FULL_ACCESS
mv src dst            → WORKSPACE_WRITE
git commit -m msg     → WORKSPACE_WRITE
cat README.md         → READ_ONLY
grep pattern file     → READ_ONLY
ls -la                → READ_ONLY
sudo reboot           → FULL_ACCESS
curl https://…        → FULL_ACCESS
```

Add as `test_classify_command_table` — one `check()` per row, runs without
spawning any subprocess.

### 2b — `prompt_assembly` ancestor walk boundary

Set up a temp tree:
```
tmp/
  .git/               ← git boundary
  CLAUDE.md           ← parent guidelines (should NOT be loaded by subagent)
  sub-project/
    workspace/
      AGENTS.md       ← correct file (should be loaded)
      src/
        deep/         ← start_dir for the walk
```

Assert:
- Walk from `deep/` finds `AGENTS.md`, not `CLAUDE.md`
- Walk from `workspace/` finds `AGENTS.md`
- Walk from `sub-project/` finds nothing (no guidelines in that dir)

### 2c — Harness mock loop runs end-to-end

Import `Harness` directly from the scaffolded template (use `importlib` with a
`sys.path` insert into a temp-scaffolded dir, same pattern as `test_skill.py`).

Run `Harness(workspace_dir=tmp, is_mock=True).run(goal="test run")`:
- `exit_reason` == `"done"` (mock loop finishes in 4 iterations)
- `.harness/<session>.jsonl` exists and contains ≥ 1 line
- Each JSONL line is valid JSON

### 2d — Context compaction triggers

Import `ContextManager`. Set `max_tokens=10` (tiny budget). Build a message list
that exceeds the budget. Assert `should_compact()` returns `True`. Call
`compact()` and assert the result is shorter than the input but still contains
the system message.

### 2e — Hook veto blocks tool execution

Import `HookRegistry`. Register a pre-hook that always returns `(False, "blocked")`.
Call `dispatch_pre_hooks("write_file", {}, workspace_trusted=True)`.
Assert `allowed == False`.

Register a post-hook that appends to a list. Call `dispatch_post_hooks`.
Assert the list was appended.

## Architecture

All new tests follow the same pattern as existing ones: stdlib only, `subprocess`
for CLI tests, direct `import` for module-level tests using `sys.path` tricks.
No new files needed — append to `test_skill.py`.

New test functions:

```
test_classify_command_table
test_prompt_assembly_boundary
test_harness_mock_loop
test_context_compaction_triggers
test_hook_veto_blocks_execution
```

## Related Code Files

- **Modify:** `test_skill.py` — append 5 new test functions, add to `TESTS` list
- **Read:** `skills/templates/harness.py`, `context_manager.py`, `hooks.py`, `prompt_assembly.py`

## Implementation Steps

1. Read all four template modules to understand import surface.
2. Write `test_classify_command_table` — pure function test, no subprocess.
3. Write `test_prompt_assembly_boundary` — temp dir tree, direct import.
4. Write `test_harness_mock_loop` — scaffold to temp, import, run mock.
5. Write `test_context_compaction_triggers` — direct import, tiny budget.
6. Write `test_hook_veto_blocks_execution` — direct import, hook registry.
7. Add all 5 to `TESTS` list.
8. Run `py test_skill.py` — target: 15/15.

## Success Criteria

- [ ] 5 new tests added, all passing
- [ ] `test_skill.py` total: 15/15 (10 existing + 5 new)
- [ ] No new external dependencies introduced
- [ ] Tests run on Windows (py), Linux/macOS (python3) without modification

## Risk Assessment

Direct import of template modules requires a scaffolded harness dir in a temp path
and careful `sys.path` manipulation. If module imports fail due to relative imports
within templates, tests must either invoke via subprocess or adjust the import path.
The existing `test_scaffold_creates_hk_cli` test uses subprocess for the same reason —
follow that pattern as fallback for the loop test.
