---
phase: 4
title: "Repo Hygiene"
status: pending
priority: P2
effort: "30m"
dependencies: []
---

# Phase 4: Repo Hygiene

## Overview

Four small but visible issues: a dangling deleted file, a missing `.gitignore`
entry, the repo's lack of governance files (which causes the 0/100 self-score),
and a minor semantic gap in `persistence.py` replay.

---

## Task 4a — Commit `js/main.js` deletion

Git status shows `D js/main.js` — the file was deleted in the working tree but
the deletion was never staged and committed. This leaves the repo in a dirty
state and the file still appears in `git log` as if it exists.

**Steps:**
1. Verify no other file depends on `js/main.js` (check `*.html` `<script>` tags).
2. Stage the deletion: `git add js/main.js` (or `git rm js/main.js`).
3. Include in the Phase 4 commit.

---

## Task 4b — Add `add-in-demo/node_modules` to `.gitignore`

The root `.gitignore` excludes `node_modules/` but the add-in demo's
`node_modules/` is a nested project. Verify whether it is already tracked:

```bash
git ls-files add-in-demo/node_modules/ | head -5
```

If tracked, remove from index without deleting:
```bash
git rm -r --cached add-in-demo/node_modules/
```

Then add to `.gitignore`:
```
add-in-demo/node_modules/
```

If already untracked, just add the `.gitignore` entry as a preventive measure.

---

## Task 4c — Add `AGENTS.md` at repo root

The harness-kit repo scores 0/100 on its own validator because it has no
`AGENTS.md`, `feature_list.json`, etc. The kit is a *skill*, not a
managed project, so a full harness is inappropriate — but a minimal governance
file explains the repo's startup workflow, scope rules, and verification commands
to any agent working in this repo.

**File: `AGENTS.md`** at repo root, minimal:

```markdown
# Harness Kit — Agent Instructions

## Startup Workflow

1. Read `skills/SKILL.md` to understand what this repo delivers.
2. Check `plans/` for any active plan; resume if one exists.
3. Run `py test_skill.py` to verify the current state before any change.

## Scope Rules

- One active task at a time. Agree scope with the user before coding.
- Only modify files under `skills/` and `test_skill.py` for skill changes.
- Do not modify `add-in-demo/` unless the task explicitly targets it.

## Verification Commands

```bash
# Windows
py test_skill.py
py skills/scripts/validate_harness.py --target . --harness-dir skills/templates --min-score 0 --json

# macOS / Linux
python3 test_skill.py
python3 skills/scripts/validate_harness.py --target . --harness-dir skills/templates --min-score 0 --json
```

## Definition of Done

A change is done only when:
- [ ] `py test_skill.py` exits 0 (all tests pass)
- [ ] No new external dependencies introduced
- [ ] The changed template files compile: `py -m py_compile skills/templates/*.py`

## End of Session

Update `plans/` with progress. Note any blockers in the relevant phase file.
```

This file alone will push the harness score from 0 to ~60 by satisfying the
Instructions and Verification subsystems.

---

## Task 4d — Fix silent JSONL skip in `persistence.py`

`replay_events` silently skips malformed lines:

```python
except json.JSONDecodeError:
    continue  # silent
```

A silent skip means a corrupted log goes undetected. Change to print a warning:

```python
except json.JSONDecodeError as exc:
    print(f"[SessionLogger] Warning: skipped malformed JSONL line: {exc}", file=sys.stderr)
    continue
```

Also add `import sys` at the top of `persistence.py`.

**File:** `skills/templates/persistence.py`

---

## Related Code Files

- **Delete (stage):** `js/main.js`
- **Modify:** `.gitignore` — add `add-in-demo/node_modules/`
- **Create:** `AGENTS.md` at repo root
- **Modify:** `skills/templates/persistence.py` — warn on malformed JSONL

## Implementation Steps

1. Check `git ls-files add-in-demo/node_modules/` — remove from index if tracked.
2. Add `add-in-demo/node_modules/` to `.gitignore`.
3. Stage `js/main.js` deletion.
4. Write `AGENTS.md` at repo root.
5. Update `persistence.py` replay with stderr warning.
6. Run `py test_skill.py` — 15/15 must pass.
7. Run `py skills/scripts/validate_harness.py --target . --harness-dir skills/templates --json`
   and confirm score ≥ 60.
8. Commit all four changes together (they belong to the same hygiene pass).

## Success Criteria

- [ ] `git status` shows no untracked deletions
- [ ] `add-in-demo/node_modules/` absent from `git ls-files`
- [ ] `AGENTS.md` at repo root, validator recognizes it
- [ ] `py skills/scripts/validate_harness.py --target . --harness-dir skills/templates --json` → `overall ≥ 60`
- [ ] `persistence.py` emits stderr warning on bad JSONL (not silent)
- [ ] All 15 tests pass

## Risk Assessment

Low risk overall. The only tricky item is `node_modules/` — if it was previously
committed, `git rm -r --cached` will stage hundreds of deletions. Do a dry-run
first (`git rm -r --cached --dry-run add-in-demo/node_modules/ | wc -l`) to gauge
size before committing.
