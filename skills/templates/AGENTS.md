# Agent Operating Manual

This file is the contract every AI agent (Claude Code, Cursor, Codex, Windsurf, Antigravity) follows when working in this repository.

## Startup Workflow

Before writing code, do the following in order:

1. Read this file (`AGENTS.md`) end-to-end.
2. Open `feature_list.json` and pick the single feature whose `status` is `in_progress`. If none, promote the first `pending` feature.
3. Open `progress.md` to recover the previous session's `Current State`, `What I Did`, and `Next Step`.
4. Run the Verification Commands (`./init.sh` on POSIX, `./init.ps1` on Windows) and capture the command and output as Evidence.

## Stay in Scope

- **One feature at a time** (one-feature-at-a-time rule). Do not modify code or docs unrelated to the active feature.
- Feature dependencies are tracked in `feature_list.json` under each feature's `dependencies` array. Resolve them in declared order.
- If you discover work that belongs to a different feature, append a new entry to `feature_list.json` with `status: "pending"` instead of doing it now.

## Definition of Done

A feature is done only when ALL of the following are true:

- The implementation builds, type-checks, lints, and compiles without errors (run via `./init.sh` / `./init.ps1`).
- All tests pass (`pytest`, `vitest`, `go test`, `cargo test`, `dotnet test` — whichever applies).
- `feature_list.json` status flipped to `"done"`.
- `progress.md` records the Verification Evidence (command and output).
- `session-handoff.md` updated with `Blockers`, `Files` touched, and `Next Session` plan.

## Verification Commands

Always run the project init script before claiming done. It must fail fast (`set -e` on POSIX, `$ErrorActionPreference = 'Stop'` on Windows). Sample:

```bash
./init.sh        # POSIX: runs build, lint, compile, test
./init.ps1       # Windows PowerShell equivalent
```

Capture stdout and stderr as command-and-output Evidence inside `progress.md`.

## End of Session

Before ending the session:

1. Update `progress.md` — fill in `Last Updated`, `Current Objective`, `Recommended Next Step`.
2. Update `session-handoff.md` — note `Blockers`, `Files` touched, and `Next Session` plan.
3. Leave the workspace in a clean, restartable state so the Next steps continue without context loss.
