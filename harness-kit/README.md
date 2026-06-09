# harness-kit

A zero-dependency, standard-library-only Python-based Agent Harness skill for AI coding agents.

It helps a repository provide a highly secure, resilient, and persistent execution loop for agents working in IDEs like Cursor, Codex, Claude Code, and Antigravity.

## Install

```bash
npx skills add walkinglabs/learn-harness-engineering --skill harness-kit
```

Or copy `skills/harness-kit/` into your skill path.

## Use

```bash
# Verify Python syntax of the templates
py -m py_compile skills/harness-kit/templates/*.py

# Run mock simulation showcasing the 9 components
py -m skills.harness-kit.templates.harness --mock --goal "Create a simple calculator class"
```

The scripts and templates use only Python standard library modules. They can be run out-of-the-box in any Python 3.8+ environment without requiring `pip install`.

## What It Contains

The skill provides standard-library-only implementation templates for the 9 core components of a modern harness:
- `harness.py` — The outer orchestration loop (While Loop).
- `context_manager.py` — Context token counting and reactive compaction.
- `tool_registry.py` — Built-in primitives (read/write/shell) and safety classifications.
- `persistence.py` — Append-only JSON Lines event logging and session replay.
- `hooks.py` — Pre-tool and post-tool lifecycle extension hooks.
- `subagent.py` — Isolated sub-agent session runner.
- `prompt_assembly.py` — Prefix-caching friendly system prompt assembler.

## Status

- [x] Zero-dependency Python templates
- [x] Mock simulation loop
- [x] Append-only event persistence
- [x] Dynamic command classification
- [x] Pre-tool and post-tool lifecycle hooks
- [x] Single-level sub-agent isolation
- [x] Vietnamese user guide (`README-VI.md`)

## Files

```text
harness-kit/
├── SKILL.md
├── README.md
├── README-VI.md
├── metadata.json
├── references/
│   ├── architecture-principles.md
│   └── concurrency-and-safety.md
└── templates/
    ├── harness.py
    ├── context_manager.py
    ├── tool_registry.py
    ├── persistence.py
    ├── hooks.py
    ├── subagent.py
    └── prompt_assembly.py
```

## Boundaries

This skill is for harness runtime implementation and execution loop engineering. It is not for general application logic, complex multi-agent frameworks (e.g., LangGraph), or prompt tuning in isolation.
