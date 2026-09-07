# Harness Kit — Agent Instructions

## Startup Workflow

1. Read `skills/SKILL.md` to understand what this repo delivers.
2. Check `plans/` for any active plan; resume the first non-completed plan found.
3. Run the verification command below before any change.

## Scope Rules

- One active task at a time. Agree scope with the user before writing code.
- Skill changes → `skills/` and `test_skill.py` only.
- Add-in example changes → `add-in-demo/` only.
- Do not cross boundaries without explicit user instruction.

## Verification Commands

```bash
# Windows
py test_skill.py
py skills/scripts/validate_harness.py --target . --harness-dir skills/templates --min-score 60 --json

# macOS / Linux
python3 test_skill.py
python3 skills/scripts/validate_harness.py --target . --harness-dir skills/templates --min-score 60 --json
```

## Definition of Done

A change is done only when:

- [ ] `py test_skill.py` exits 0 (all tests pass)
- [ ] No new external dependencies introduced in `skills/`
- [ ] Changed template files compile: `py -m py_compile skills/templates/*.py`

## State Artifacts

| File | Purpose |
|------|---------|
| `feature_list.json` | Active features for this repo |
| `progress.md` | Current State, What I Did, Recommended Next Step |
| `session-handoff.md` | Blockers, Files changed, Next Session goal |
| `plans/` | Active implementation plans (phase files) |
| `plans/reports/` | Audit and research reports |
| `test_skill.py` | Regression suite — run before and after every change |

## End of Session

Note progress in the relevant phase file under `plans/`. If blocked, document
the blocker and the last known good state.
