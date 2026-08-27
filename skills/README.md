# harness-kit

A standard-library-only Python agent harness, plus a small skill for scaffolding and auditing it.

It helps a repository give AI coding agents (Claude Code, Cursor, Codex, Windsurf, Antigravity) five things they need to be effective: instructions, state, verification, scope boundaries, and lifecycle handoff.

## Install

Run this one-liner from the **project root** — governance files only (any language/stack):

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/nguyenanh92/harness-kit/main/install.ps1 | iex
```

Add `--full` to also scaffold the Python runtime (agent loop, sub-agents, hooks).

Or clone and run scripts directly:

```bash
git clone https://github.com/nguyenanh92/harness-kit.git
python3 skills/scripts/scaffold_harness.py --target /path/to/project
```

Python 3.8+ is the only requirement. No `pip install`, no `npm install`.

## Use

```bash
# via hk.py (ships with every project after install)
py hk.py feature "New screen"   # add a feature
py hk.py start F-001            # set active
py hk.py status                 # show queue + next tip
py hk.py done                   # verify then mark done
py hk.py audit                  # score the harness

# or invoke scripts directly
python3 skills/scripts/validate_harness.py --target /path/to/project
python3 skills/scripts/run_benchmark.py    --target /path/to/project --html report.html
python3 skills/scripts/render_assessment_html.py --target /path/to/project
```

On Windows use `py` instead of `python3`.

## What It Creates

The scaffold writes governance files at the project root and code modules under `harness/` (with `--full`):

Project root (governance):

- `AGENTS.md` (or `CLAUDE.md`) — startup workflow, working rules, Definition of Done
- `feature_list.json` + `feature-list.schema.json` — features and dependency graph
- `progress.md` — Current State, What I Did, Verification Evidence, Recommended Next Step
- `session-handoff.md` — Blockers, Files, Next Session
- `init.sh` / `init.ps1` — fail-fast verification (compile + test)
- `hk.py` — stdlib-only CLI (feature / start / status / done / audit)

`<harness-dir>/` (code, default `harness/`):

- `harness.py` — bounded while-loop orchestrator
- `context_manager.py` — token budget and compaction
- `tool_registry.py` — permission gate and built-in primitives
- `persistence.py` — append-only JSONL session log
- `hooks.py` — pre/post-tool lifecycle hooks with trust gate
- `subagent.py` — isolated single-level sub-agents
- `prompt_assembly.py` — caching-friendly guidelines aggregator
- `__init__.py`

## What It Checks

`validate_harness.py` scores the five harness subsystems (25 structural checks):

1. **Instructions** — `AGENTS.md` presence, startup workflow, Definition of Done, routing to state.
2. **State** — feature tracker validity, progress log restart markers, handoff completeness.
3. **Verification** — fail-fast init, test command documented, evidence recorded.
4. **Scope** — one-feature-at-a-time rule, dependency graph, completion gate.
5. **Lifecycle** — startup script, end-of-session procedure, restart markers, code modules present.

`run_benchmark.py` combines the score with eval coverage and produces a recommendation.

The score is structural — it confirms the harness is *coherent*, not that an agent actually performs better. Real effectiveness still needs before/after sessions on representative tasks.

## Status

- [x] Standard-library-only Python harness (7 code modules)
- [x] Scaffold script with `{{KEY}}` template substitution
- [x] Five-subsystem validator (no floor-1 score, word-bounded matching)
- [x] HTML assessment report
- [x] Structural benchmark with eval-coverage proxy
- [x] Mock simulation loop in `harness.py`
- [x] 10 eval cases
- [x] Vietnamese references (`README-VI.md`, `SKILL.md.vi`, `nine-components.vi.md`)
- [x] One-liner install scripts (`install.sh` / `install.ps1`) with `--full` flag
- [x] `hk.py` — universal workflow CLI shipped with every scaffolded project

## Files

```text
skills/
├── SKILL.md
├── SKILL.md.vi
├── README.md
├── README-VI.md
├── metadata.json
├── agents/
│   └── openai.yaml
├── evals/
│   └── evals.json
├── scripts/
│   ├── scaffold_harness.py
│   ├── validate_harness.py
│   ├── render_assessment_html.py
│   ├── run_benchmark.py
│   └── lib/
│       ├── __init__.py
│       └── harness_utils.py
├── templates/
│   ├── AGENTS.md
│   ├── feature_list.json
│   ├── feature-list.schema.json
│   ├── progress.md
│   ├── session-handoff.md
│   ├── init.sh
│   ├── init.ps1
│   ├── hk.py
│   └── (Python modules)
└── references/
    ├── architecture-principles.md
    ├── nine-components.md
    ├── nine-components.vi.md
    ├── tool-registry-and-safety.md
    ├── context-and-memory.md
    ├── lifecycle-and-hooks.md
    └── gotchas.md
```

## Boundaries

This skill is for harness runtime engineering — the bounded loop, tool safety, persistence, and the documents that bind an agent's session. It is not for general application logic, multi-agent frameworks like LangGraph, or prompt tuning in isolation. Keep project-specific facts in the target repository, not in the skill.
