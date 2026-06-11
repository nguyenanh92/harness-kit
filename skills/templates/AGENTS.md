# Agent Operating Manual

This is the contract every AI agent (Claude Code, Cursor, Codex, Windsurf, Antigravity) follows when working in this repository.

## Startup Workflow

Before writing code, in order:

1. Read this file (`{{AGENT_FILE_NAME}}`) end-to-end.
2. Open `feature_list.json` and pick the single feature whose `status` is `in_progress`. If none, promote the first `pending` feature.
3. Open `progress.md` to recover the previous session's `Current State`, `What I Did`, and `Recommended Next Step`.
4. Run the verification entrypoint (`{{PRIMARY_VERIFICATION_COMMAND}}`) and capture the command and output as Evidence.

## Stay in Scope

- **One feature at a time** (one-feature-at-a-time rule). Do not modify code or docs unrelated to the active feature.
- Feature dependencies are tracked in `feature_list.json` under each feature's `dependencies` array. Resolve them in declared order.
- If you discover work that belongs to a different feature, append a new entry to `feature_list.json` with `status: "pending"` instead of doing it now.

## Definition of Done

A feature is `done` only when ALL of the following are true:

- The implementation builds, type-checks, lints, and compiles without errors (`./init.sh` / `./init.ps1`).
- All tests pass (`pytest`, `unittest discover`, `vitest`, `go test`, `cargo test`, `dotnet test` — whichever applies).
- `feature_list.json` status flipped to `"done"`.
- `progress.md` records the Verification Evidence (command and output).
- `session-handoff.md` lists `Blockers`, `Files` touched, and `Next Session` plan.

## Verification Commands

Always run the project init script before claiming done. It must fail fast (`set -e` on POSIX, `$ErrorActionPreference = 'Stop'` on Windows):

```bash
./init.sh        # POSIX: compile, lint, test
./init.ps1       # Windows PowerShell equivalent
```

Capture stdout and stderr as command-and-output Evidence inside `progress.md`.

## End of Session

Before ending:

1. Update `progress.md` — set `Last Updated`, `Current Objective`, `Recommended Next Step`.
2. Update `session-handoff.md` — note `Blockers`, `Files` touched, `Next Session` plan.
3. Leave the workspace in a clean, restartable state. The next agent (or future you) should be able to resume from `progress.md` + `session-handoff.md` alone.

## Harness Code Location

The zero-dependency Python harness modules live in `{{HARNESS_DIR}}/`:

- `harness.py` — orchestrator loop
- `context_manager.py` — token budget and compaction
- `tool_registry.py` — permissions and primitives
- `persistence.py` — append-only JSONL session log
- `hooks.py` — pre/post-tool callbacks
- `subagent.py` — isolated single-level sub-agents
- `prompt_assembly.py` — caching-friendly instruction aggregator

Treat that directory as the contract surface. Add new tools through `tool_registry.py`; never bypass it.
