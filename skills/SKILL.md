---
name: harness-kit
description: >-
  Design, bootstrap, and audit standard-library-only Python agent harnesses following the 9 core components:
  while loop, context compaction, tool registry, sub-agents, primitives, memory persistence,
  system prompt assembly, lifecycle hooks, and shell permission gates.
license: MIT
---

# Harness Kit

Use this skill to design, bootstrap, and audit a zero-dependency, standard-library-only Python Agent Harness. This ensures the agent loop is lightweight, highly resilient, and compatible with any execution environment (such as Cursor, Codex, Claude Code, and Antigravity).

Not for heavy multi-agent frameworks, complex general application architectures, or front-end interface design.

## Installation

To add this skill to your project workspace, run the following command using the Skills CLI:

```bash
npx skills add nguyenanh92/harness-kit --skill harness-kit
```

Or copy the `skills` directory manually into your project's `skills/` folder.

## Core Model

Every standard-library-only Python harness maps the 9 core components onto five main subsystems:

| Subsystem | Template Module | Purpose |
|---|---|---|
| Instructions | `prompt_assembly.py` | Walk ancestors for guidelines (`CLAUDE.md`) and keep prefix caching intact. |
| State | `persistence.py`, `context_manager.py` | Log events in append-only format; manage token budget and compact history. |
| Verification | Built-in primitives | Run compiler checks and test command subprocesses to verify actions. |
| Scope | `tool_registry.py`, `subagent.py` | Restrict tools, classify shell commands, spawn isolated single-level sub-agents. |
| Lifecycle | `harness.py`, `hooks.py` | Orchestrate outer `while` loop, call lifecycle hooks before/after tool runs. |

## First Move

1. **Assess the sandbox**: Check Python version and verify command-line availability (`py` or `python3`).
2. **Choose harness path**: Choose a target directory (e.g., `harness/`) to scaffold the standard library templates.
3. **Map operations**: Identify which files the agent needs to read/write and what shell commands require interactive verification.

## Common Tasks

### Scaffold a Custom Harness

Scaffold the zero-dependency Python harness templates into your project workspace:

```bash
# On Windows
py -m skills.scripts.scaffold_harness --target harness

# On macOS/Linux
python3 -m skills.scripts.scaffold_harness --target harness
```

Options:
- `--target DIR`: Destination folder to write the harness files (default: `harness`).
- `--force`: Overwrite existing files in the target directory.

### Audit and Validate an Existing Harness

Audit and score your workspace harness across the 5 structural subsystems (Instructions, State, Verification, Scope, Lifecycle):

```bash
# On Windows
py -m skills.scripts.validate_harness --target harness

# On macOS/Linux
python3 -m skills.scripts.validate_harness --target harness
```

Options:
- `--json`: Output the score breakdown in JSON format.
- `--html FILE`: Render and write a visual HTML report to the specified file path.
- `--min-score SCORE`: Exit with error if score is below threshold (default: 70).

### Verify Template Syntax

Check that all python files in the template directory are syntactically valid:

```bash
# On Windows PowerShell
Get-ChildItem -Path "skills/templates/*.py" | ForEach-Object { py -m py_compile $_.FullName }

# On macOS/Linux
python3 -m py_compile skills/templates/*.py
```

### Run Mock Simulation Loop

Run the harness in simulation mode to test the while loop, pre/post hooks, sub-agent spawning, and compaction:

```bash
# On Windows
py -m skills.templates.harness --mock --goal "Create a simple calculator class"

# On macOS/Linux
python3 -m skills.templates.harness --mock --goal "Create a simple calculator class"
```

### Clean Up Simulation Logs

To delete temporary session files and folders created during the simulation run:

```bash
# Windows
Remove-Item -Path "calculator.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path ".harness" -Recurse -Force -ErrorAction SilentlyContinue

# macOS / Linux
rm -f calculator.py
rm -rf .harness
```

## When to Read References

Load only the reference documentation needed for the specific design problem:

- General setup, loop orchestration, and append-only logging: [Architecture Principles](references/architecture-principles.md)
- Command classification, permission levels, and sub-agent forks: [Concurrency & Safety](references/concurrency-and-safety.md)
- Deep-dive explanation of the 9 core components and how they map to the 5 subsystems: [Agent Harness Deep Dive](references/agent-harness-deep-dive.md)

## Working Rules for AI Agents

When any AI Agent (e.g., Claude Code, Cursor, Windsurf, Antigravity) loads this skill in a workspace, the agent MUST strictly adhere to the following workflow to maintain scope and prevent breaking the codebase:

1. **Read Guidelines First**: Read the `AGENTS.md` or `CLAUDE.md` file at the root of the project to understand workspace rules.
2. **Stay in Scope**: Read `feature_list.json` to find the active feature. Focus on ONLY one feature at a time. Never modify files unrelated to the active feature.
3. **Update Progress Log**: Document the current state, modifications, and the next steps in `progress.md` before ending the session.
4. **Mandatory Verification**: Run verification tests (e.g., `./init.sh` or validate via `py .agents/skills/harness-kit/scripts/validate_harness.py --target harness`) and output the test execution evidence before claiming a task is done.

## Design Rules

- **Zero External Dependencies**: Never import third-party packages in core harness modules. Stick to Python standard libraries.
- **Prefix Caching Alignment**: Static system prompt text must be loaded first, with dynamic contents appended later to protect prompt cache.
- **Append-only Logging**: Flush events to disk immediately. Replay logs line-by-line to restore state.
- **Single-level Spawning Invariant**: Child sub-agents must not be allowed to spawn further sub-agents. Disable the spawn tool in children.
- **Manual Gate Default**: Default to interactive console prompts (`input()`) for commands containing dangerous patterns like `rm`, `sudo`, `curl`.

## Deliverable Checklist

When building or auditing a Python-based harness, ensure the target repository includes:

- [ ] `harness.py` — orchestrator loop
- [ ] `context_manager.py` — token tracking and compaction
- [ ] `tool_registry.py` — permission checks and primitives
- [ ] `persistence.py` — append-only JSON Line logging
- [ ] `hooks.py` — pre-tool and post-tool lifecycle callbacks
- [ ] `subagent.py` — isolated sub-agent context
- [ ] `prompt_assembly.py` — caching-friendly instructions aggregator
- [ ] A local `.harness/` directory containing session logs
