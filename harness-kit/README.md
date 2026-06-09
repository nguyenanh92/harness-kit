# harness-kit

A zero-dependency, standard-library-only Python-based Agent Harness implementation for AI coding agents.

It helps a repository provide a highly secure, resilient, and persistent execution loop for agents working in IDEs like Cursor, Codex, Claude Code, and Antigravity.

## Install

```bash
npx skills add nguyenanh92/harness-kit --skill harness-kit
```

Or copy `skills/harness-kit/` into your skill path.

## Use

```bash
# Scaffold the Python templates into a target directory
py -m skills.harness-kit.scripts.scaffold_harness --target /path/to/project/harness

# Validate and score your project's harness
py -m skills.harness-kit.scripts.validate_harness --target /path/to/project/harness

# Run mock simulation loop showcasing 9 components
py -m skills.harness-kit.templates.harness --mock --goal "Create a simple calculator class"
```

The scripts use only Python standard library modules. They can be run after copying the skill directory into another repository.

## What It Creates

- `harness.py` — Main orchestrator loop
- `context_manager.py` — Token track and compaction
- `tool_registry.py` — Permission gates and primitives
- `persistence.py` — Append-only JSON Lines logger
- `hooks.py` — Pre-tool and post-tool lifecycle hooks
- `subagent.py` — Isolated sub-agent session context
- `prompt_assembly.py` — Caching-friendly guidelines aggregator

## What It Checks

`validate_harness.py` scores the five harness subsystems:

1. Instructions
2. State
3. Verification
4. Scope
5. Lifecycle

The score is structural. It tells you whether the harness is present and coherent; it does not replace real before/after agent-session testing.

## Status

- [x] Zero-dependency Python templates
- [x] Scaffolding script
- [x] Five-subsystem validation script
- [x] HTML assessment report generator
- [x] Append-only event persistence
- [x] Mock simulation loop
- [x] 10 eval cases
- [x] Vietnamese user guide (`README-VI.md`)

## Files

```text
harness-kit/
├── SKILL.md
├── README.md
├── README-VI.md
├── metadata.json
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── scaffold_harness.py
│   └── validate_harness.py
├── templates/
│   ├── harness.py
│   ├── context_manager.py
│   ├── tool_registry.py
│   ├── persistence.py
│   ├── hooks.py
│   ├── subagent.py
│   └── prompt_assembly.py
├── references/
│   ├── architecture-principles.md
│   └── concurrency-and-safety.md
└── evals/
    └── evals.json
```

## Boundaries

This skill is for harness runtime implementation and execution loop engineering. It is not for general application logic, complex multi-agent frameworks (e.g., LangGraph), or prompt tuning in isolation. Keep project-specific facts in the target repository.
