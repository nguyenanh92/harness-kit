# Learn Harness Engineering - Agent Skills

This repository contains reusable AI agent skills designed for harness engineering. Each skill is a standalone prompt template that can be loaded by AI coding agents such as Claude Code, Codex, Cursor, and Antigravity.

## Available Skills

### 1. [harness-creator](harness-creator/README.md)

A production-grade harness engineering skill to scaffold, audit, and benchmark coding-agent harnesses.
- **Subsystems**: Instructions, State, Verification, Scope, and Lifecycle.
- **Templates**: `AGENTS.md`, `feature_list.json`, `progress.md`, `init.sh`, and `session-handoff.md`.
- **Scripts**: Scaffolding, validation, HTML reporting, and structural benchmarking (Node.js).

### 2. [harness-kit](harness-kit/README.md)

A zero-dependency, standard-library-only Python-based Agent Harness implementation.
- **9 Core Components**: Bounded while loop, context compaction, tool registry, sub-agent isolation, filesystem/shell primitives, append-only durability, system prompt assembly, lifecycle hooks, and shell command permission gating.
- **Templates**: `harness.py`, `context_manager.py`, `tool_registry.py`, `persistence.py`, `hooks.py`, `subagent.py`, and `prompt_assembly.py`.
- **Scripts**: Python scaffolding and five-subsystem validation.

---

## How Skills Work

Each skill is organized in a standardized folder structure:
1. **`SKILL.md`** — The main entry point, containing YAML metadata frontmatter and prompt instructions for the agent.
2. **`references/`** — Supporting reference documents loaded by the agent on demand.
3. **`templates/`** — Initial file templates that the skill scaffolds.
4. **`scripts/`** — Scaffolding and verification CLI tools.
5. **`evals/`** — Standardized evaluation test cases for the skill.
6. **`agents/`** — Configuration interfaces for exposing the skill.

Skills use progressive disclosure: the agent initially loads only the name and description. It reads `SKILL.md` when activated, and accesses referenced assets only when required.

## Security

All files in this repository are audited for safety:
- No hidden backdoors, obfuscated URLs, or encrypted payloads.
- No credential leaks or hardcoded secrets.
- No command injection vulnerabilities.
- Scripts rely only on built-in standard modules.

## License

MIT
