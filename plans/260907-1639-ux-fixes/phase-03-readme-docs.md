---
phase: 3
title: "README install documentation"
status: pending
priority: P2
effort: "45m"
dependencies: []
---

# Phase 3: README install documentation

## Problem

The README shows only the bare install commands with no flag examples:

```bash
# macOS / Linux
curl -fsSL .../install.sh | sh

# Windows (PowerShell)
irm .../install.ps1 | iex
```

Three gaps:
1. `--full` flag: mentioned only in a blockquote footnote, never shown as a runnable command
2. Pipe flag-passing syntax: `sh -s -- --full` (POSIX) and the Windows alternative
   are not documented anywhere in the README
3. `--agent-file CLAUDE.md`: mentioned in the blockquote but no runnable example

## Fix — Expand the Install section

Replace the current Install block with:

````markdown
## Install

Run from your **project root**:

```bash
# macOS / Linux — governance files only (recommended for most projects)
curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh

# macOS / Linux — with Python runtime (harness loop, sub-agents, hooks)
curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh -s -- --full

# macOS / Linux — if your AI reads CLAUDE.md instead of AGENTS.md
curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh -s -- --agent-file CLAUDE.md
```

```powershell
# Windows PowerShell — governance files only
irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1 | iex

# Windows PowerShell — with flags (--full, --agent-file, --force)
& ([ScriptBlock]::Create((irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1))) --full
& ([ScriptBlock]::Create((irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1))) --agent-file CLAUDE.md
```

**Requirements:** Python 3.8+, git

| Flag | Default | Effect |
|------|---------|--------|
| _(none)_ | governance only | 6 files: AGENTS.md, feature\_list.json, progress.md, init.sh/ps1, session-handoff.md, hk.py |
| `--full` | off | Also installs the Python harness runtime (harness/ dir with 7 modules) |
| `--agent-file CLAUDE.md` | AGENTS.md | Write CLAUDE.md instead of AGENTS.md (Claude Code default) |
| `--force` | off | Overwrite existing files |
````

## Additional: callout for Windows pipe limitation

Add a note immediately below the Windows block explaining WHY the `& ([ScriptBlock]::Create(...))` syntax is needed — `irm | iex` creates a new pipeline scope that doesn't receive arguments:

```markdown
> **Windows note:** `irm ... | iex` does not forward arguments to the script.
> Use the `[ScriptBlock]::Create(...)` form shown above when passing flags.
```

## Files

- **Modify:** `README.md` — Install section (lines 26–52)

## Implementation Steps

1. Read current README Install section (lines 26–52) to confirm exact content.
2. Replace with the expanded block above.
3. Verify Markdown renders correctly (table, code fences, blockquote).
4. No tests needed — docs-only change.

## Success Criteria

- [ ] All 3 flag variants shown for macOS/Linux with correct `sh -s --` syntax
- [ ] All 3 flag variants shown for Windows with `[ScriptBlock]::Create` form
- [ ] Flag table explains governance-only vs full
- [ ] Windows pipe limitation explained in a note
- [ ] No broken links or malformed Markdown

## Risk Assessment

Docs-only. Zero functional risk. The Windows `[ScriptBlock]::Create` syntax
has been verified in install.ps1 comments — it is the canonical workaround.
