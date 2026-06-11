---
name: harness-kit
description: >-
  Design, bootstrap, and audit standard-library-only Python agent harnesses
  built around the 9 core components: while loop, context compaction, tool
  registry, sub-agents, primitives, memory persistence, system prompt
  assembly, lifecycle hooks, and shell permission gates.
license: MIT
---

# Harness Kit

Use this skill to build a repository where any coding agent (Claude Code, Cursor, Codex, Windsurf, Antigravity) can start fast, stay in scope, verify its work, and resume across sessions — backed by a zero-dependency Python harness.

Not for heavy multi-agent frameworks, general application architecture, or front-end UI design.

## Core Model

A harness has nine internal components mapped onto five external subsystems. The validator scores the subsystems; the templates ship the components.

| Subsystem      | Minimal artifact                                  | Purpose |
|----------------|---------------------------------------------------|---------|
| Instructions   | `AGENTS.md` (or `CLAUDE.md`)                      | Startup workflow, working rules, Definition of Done |
| State          | `feature_list.json`, `progress.md`                | Active feature, status, evidence, next step |
| Verification   | `init.sh` / `init.ps1`                            | Tests, compiles, lints — fails fast before claiming done |
| Scope          | Feature dependencies + Definition of Done         | One feature at a time; no half-finished work |
| Lifecycle      | `session-handoff.md`, end-of-session routine      | Makes the next session restartable |

Code modules (`harness.py`, `tool_registry.py`, `persistence.py`, ...) live under `harness/`. Governance files (`AGENTS.md`, `feature_list.json`, ...) live at the project root.

## First Move

1. Inspect what already exists: instruction files, feature list, init script, the harness directory if any.
2. Ask only for missing context that cannot be inferred: agent file name (AGENTS.md vs CLAUDE.md), harness directory name, whether overwriting is allowed.
3. Scaffold minimally first. Add hooks, sub-agents, or benchmarking only when the user's problem calls for them.

## Common Tasks

All scripts are standard-library Python. Use `py` on Windows, `python3` elsewhere.

### Scaffold a harness

```bash
python3 skills/scripts/scaffold_harness.py --target /path/to/project
```

Options:

- `--harness-dir harness` — where the 9 Python modules live (default: `harness`).
- `--agent-file CLAUDE.md` — write `CLAUDE.md` instead of `AGENTS.md`.
- `--governance-only` — emit governance files only, no code modules.
- `--force` — overwrite existing files (confirm with the user first).

After scaffolding, the project root contains `AGENTS.md`, `feature_list.json`, `progress.md`, `session-handoff.md`, `init.sh`, `init.ps1`, and `feature-list.schema.json`. The harness directory contains the seven Python modules plus `__init__.py`.

### Audit a harness

```bash
python3 skills/scripts/validate_harness.py --target /path/to/project
```

Reports an overall score (0–100), the lowest-scoring subsystem (the "bottleneck"), and pass/fail for each of 25 structural checks. Use `--json` for machine output and `--html report.html` for a self-contained report.

Treat the lowest score as a *candidate* bottleneck. Confirm with failing tasks or session logs before claiming causality.

For CI, raise the threshold: `--min-score 90` is realistic for a maintained harness; the default `70` is starter-friendly and lets early-stage projects pass.

### Produce a benchmark report

```bash
python3 skills/scripts/run_benchmark.py --target /path/to/project --html report.html
```

Combines the structural score with eval coverage (`evals/evals.json`) and a recommendation. The output is structural — real effectiveness still requires before/after agent sessions on representative tasks.

### Render the HTML assessment alone

```bash
python3 skills/scripts/render_assessment_html.py --target /path/to/project --output report.html
```

## When to Read References

Load only the reference needed for the user's problem:

- High-level invariants (zero-dep, bounded loop, append-only log): [Architecture Principles](references/architecture-principles.md)
- What each module does and where to extend: [Nine Components](references/nine-components.md) (also [Vietnamese](references/nine-components.vi.md))
- Permissions, classification, sub-agent forks: [Tool Registry and Safety](references/tool-registry-and-safety.md)
- Compaction, prefix cache, JSONL persistence: [Context and Memory](references/context-and-memory.md)
- Bootstrap stages, hooks, restart contract: [Lifecycle and Hooks](references/lifecycle-and-hooks.md)
- Non-obvious failure modes (numbered): [Gotchas](references/gotchas.md)

## Design Rules

- **Zero external dependencies** in core harness modules. Standard library only.
- **Prefix caching alignment**: static prompt first, dynamic content appended; never rewrite the prefix.
- **Append-only logging**: flush every event immediately; replay reconstructs context, not side effects.
- **Single-level sub-agent fork**: children must not be able to spawn further children.
- **Fail-closed permission gate**: unknown commands escalate; trust is all-or-nothing per workspace.
- **One active feature**: enforced by `feature_list.json`, not by hope.
- **Never hide destructive behavior in scripts**: `--force` is opt-in; ask before overwriting.

## Deliverable Checklist

A usable harness leaves the target project with:

- [ ] `AGENTS.md` (or `CLAUDE.md`) — startup, scope rules, Definition of Done, end-of-session
- [ ] `feature_list.json` + `feature-list.schema.json` — features with id/name/description/status/dependencies
- [ ] `progress.md` — Current State, What I Did, Verification Evidence, Recommended Next Step
- [ ] `session-handoff.md` — Blockers, Files, Next Session
- [ ] `init.sh` / `init.ps1` — fail-fast verification (compile + test)
- [ ] `<harness-dir>/` containing `harness.py`, `context_manager.py`, `tool_registry.py`, `persistence.py`, `hooks.py`, `subagent.py`, `prompt_assembly.py`
- [ ] A `.harness/` directory created on first run by `SessionLogger`

If you cannot create files, output exact file contents and commands instead.
