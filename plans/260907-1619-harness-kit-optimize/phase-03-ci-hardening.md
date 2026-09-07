---
phase: 3
title: "CI Hardening"
status: pending
priority: P2
effort: "45m"
dependencies: [1, 2]
---

# Phase 3: CI Hardening

## Overview

The CI workflow exists and runs on 3 OSes × 3 Python versions, but the
`validate_harness.py` step uses `--min-score 0` and `continue-on-error: true`,
meaning the repo's own 0/100 harness score is silently ignored on every push.
Fix CI to be honest about what it checks and why.

## Problems

### 3a — Validate step produces 0/100 and continues silently

```yaml
# CURRENT (.github/workflows/test.yml lines 57–65)
- name: Score this repo's harness state
  shell: bash
  run: |
    python skills/scripts/validate_harness.py \
      --target . \
      --harness-dir skills \
      --min-score 0 \       # <-- never fails
      --json
  continue-on-error: true   # <-- failure suppressed
```

This step was likely added as an informational probe before the repo had any
governance files. After Phase 4 adds `AGENTS.md`, the score will rise. The step
should enforce a meaningful floor.

### 3b — Score target is wrong

`--harness-dir skills` tells the validator to look for Python harness modules
inside `skills/`. The validator's `list_code_modules` checks for `harness.py`,
`context_manager.py` etc. — these live in `skills/templates/`, not `skills/`.
So the code-module check always fails even though the templates exist.

Correct flag: `--harness-dir skills/templates`.

## Fixes

### Fix 3a — Raise min-score floor

After Phase 4 adds `AGENTS.md` and minimal governance, the repo should score ≥ 60.
Set `--min-score 60` and remove `continue-on-error: true`.

If future changes risk dropping below 60, the CI failure is the intended signal.

### Fix 3b — Correct harness-dir

Change `--harness-dir skills` → `--harness-dir skills/templates`.

### Fix 3c — Surface score in CI output

Add `--html` output as a build artifact so the score is visible in the GitHub
Actions summary without requiring a local run:

```yaml
- name: Score harness
  shell: bash
  run: |
    python skills/scripts/validate_harness.py \
      --target . \
      --harness-dir skills/templates \
      --min-score 60 \
      --html harness-score.html \
      --json

- name: Upload score report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: harness-score-${{ matrix.os }}-py${{ matrix.python }}
    path: harness-score.html
    retention-days: 7
```

## Related Code Files

- **Modify:** `.github/workflows/test.yml` — lines 57–65 (validate step)

## Implementation Steps

1. Read `.github/workflows/test.yml` fully before editing.
2. Replace the validate step with the hardened version above.
3. Add artifact upload step.
4. Verify YAML is syntactically valid (indent-sensitive).
5. Confirm this change only takes effect after Phase 4 adds governance files
   (otherwise CI will break at 60 floor on current 0/100 score).

## Success Criteria

- [ ] `--harness-dir` points to `skills/templates`
- [ ] `--min-score 60` enforced (no `continue-on-error`)
- [ ] HTML report uploaded as artifact on every run
- [ ] YAML valid, no syntax errors

## Risk Assessment

**Order dependency:** This phase must run after Phase 4 (governance files added).
If Phase 3 is merged before Phase 4, CI will fail at the 60 floor on the current
0/100 score. Either: (a) merge 04 first, then 03, or (b) keep `--min-score 0`
temporarily and raise it in the same commit as Phase 4.

Recommended: implement Phase 04 in the same commit as this CI change so the
floor is set and met atomically.
