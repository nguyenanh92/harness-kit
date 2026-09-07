---
phase: 1
title: "Template Bug Fixes"
status: pending
priority: P1
effort: "1h"
dependencies: []
---

# Phase 1: Template Bug Fixes

## Overview

Fix two bugs in template modules that directly contradict the kit's own gotchas documentation.
These are in `skills/templates/` — files copied into user projects at scaffold time — so bugs
here propagate to every newly scaffolded project.

## Bug 1 — `tool_registry.py`: `rm somefile` classified READ_ONLY (Gotcha #3)

### Problem

`classify_command` uses substring matching against a hardcoded list:

```python
# CURRENT (buggy)
if any(k in normalized for k in ["rm -rf", "sudo", "shutdown", "curl", "wget", "chmod"]):
    return "FULL_ACCESS"

if any(k in normalized for k in ["mkdir", "touch", "git add", "git commit", "pip install", "npm install"]):
    return "WORKSPACE_WRITE"

return "READ_ONLY"   # <-- rm somefile lands here
```

`rm somefile`, `rm -f file`, `mv`, `cp`, `dd`, `truncate`, `echo > file` all fall through
to READ_ONLY. The classifier is meant to be a *safety net*; false negatives are the
dangerous failure mode.

### Fix

1. Add `rm `, `mv `, `cp `, `dd `, `truncate ` to WORKSPACE_WRITE tier (space-suffix to
   avoid matching `rmdir` as FULL_ACCESS while still catching `rm file`).
2. Rename the check list to an ordered tuple with a comment explaining why order matters.
3. Add `curl ` and `wget ` already catch network fetches — move them to FULL_ACCESS (they already are).
4. Keep `rm -rf` in FULL_ACCESS; add `rm -r` as well (recursive without force is still destructive).
5. The fix must preserve: `grep pattern file` → READ_ONLY, `cat file` → READ_ONLY.

### Files

- **Modify:** `skills/templates/tool_registry.py` — `classify_command` method (lines 41–56)

### Acceptance Criteria

- `classify_command("rm somefile")` → `WORKSPACE_WRITE`
- `classify_command("rm -rf /tmp")` → `FULL_ACCESS`
- `classify_command("rm -r dir")` → `FULL_ACCESS`
- `classify_command("cat README.md")` → `READ_ONLY`
- `classify_command("grep pattern file.txt")` → `READ_ONLY`
- `classify_command("mv src dst")` → `WORKSPACE_WRITE`
- `classify_command("git commit -m msg")` → `WORKSPACE_WRITE`

---

## Bug 2 — `prompt_assembly.py`: ancestor walk reaches filesystem root (Gotcha #5)

### Problem

`find_guidelines_file` walks from `workspace_dir` up to the filesystem root:

```python
# CURRENT (buggy)
while True:
    # ... check for guidelines file ...
    parent_dir = current_dir.parent
    if parent_dir == current_dir:   # only stops at filesystem root
        break
    current_dir = parent_dir
```

In a nested project (`~/work/main-repo/sub-project/`), a subagent launched from
`sub-project/` will load `main-repo/CLAUDE.md` instead of (or in addition to) its own.
This leaks parent-repo guidelines into child contexts (Gotcha #5).

### Fix

Stop the walk at the first `.git` directory found **or** at `workspace_dir` itself
(take whichever terminates sooner). The walk should never cross a git repo boundary.

```python
# PROPOSED
def find_guidelines_file(self, start_dir, workspace_root=None):
    current_dir = Path(start_dir).resolve()
    stop_at = Path(workspace_root).resolve() if workspace_root else current_dir

    while True:
        for filename in self.filename_priority:
            target_path = current_dir / filename
            if target_path.is_file():
                try:
                    return target_path, target_path.read_text(encoding="utf-8")
                except Exception:
                    pass

        # Stop at git boundary or at the declared workspace root
        if (current_dir / ".git").exists() or current_dir == stop_at:
            break

        parent_dir = current_dir.parent
        if parent_dir == current_dir:   # filesystem root guard
            break
        current_dir = parent_dir

    return None, ""
```

`assemble()` passes `workspace_dir` as `workspace_root` so the walk is
bounded by default even without an explicit caller-supplied root.

### Files

- **Modify:** `skills/templates/prompt_assembly.py` — `find_guidelines_file` + `assemble` (lines 18–59)

### Acceptance Criteria

- Walk stops at `.git` boundary — subagent in `sub-project/` does NOT load `main-repo/CLAUDE.md`
- Walk still finds `AGENTS.md` / `CLAUDE.md` *inside* the workspace subtree
- Walk still finds a file at the workspace root itself
- Filesystem root guard still present (belt-and-suspenders)

---

## Implementation Steps

1. Open `skills/templates/tool_registry.py`, replace `classify_command`.
2. Open `skills/templates/prompt_assembly.py`, replace `find_guidelines_file` + update `assemble`.
3. Run `py test_skill.py` — all 10 existing tests must still pass.
4. Add targeted assertions in Phase 2 test suite for both fixes.

## Risk Assessment

- Aggressive `rm` classification could block `rm -i` (interactive) or `rm --interactive`
  from being called READ_ONLY. These are still destructive — classifying WORKSPACE_WRITE
  is correct. Low risk.
- Ancestor-walk change: if a project has no `.git` and no explicit `workspace_root`,
  the walk is bounded by `start_dir` (no walk at all). This is safer than the current
  unbounded walk.
