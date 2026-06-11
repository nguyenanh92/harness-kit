# The Nine Components

Load when you need to understand what each template module is for, or to decide where a new feature belongs.

## What "harness" means here

```
LLM  +  Harness  =  Agent
```

The LLM provides reasoning. The harness provides the loop, memory, tools, and safety rails. Drop either side and you do not have an agent.

A **framework** (LangChain, LangGraph, AutoGen) tries to be both. A **harness** stays small: it is the thinnest envelope the LLM needs to do useful work, owned by you, easy to read end-to-end. This skill ships a harness, not a framework.

## The nine components

| # | Component                | Module                  | What it owns |
|---|--------------------------|-------------------------|--------------|
| 1 | While loop               | `harness.py`            | Bounded orchestration; ties the other eight together |
| 2 | Context compaction       | `context_manager.py`    | Token estimation, threshold-based summarization |
| 3 | Tool registry            | `tool_registry.py`      | Tool descriptors, permission classifier, dispatch |
| 4 | Sub-agents               | `subagent.py`           | Fork a restricted child for a scoped sub-task |
| 5 | Primitives               | `tool_registry.py` builtins | `read_file`, `write_file`, `run_shell` |
| 6 | Memory / persistence     | `persistence.py`        | Append-only JSONL session log, replay |
| 7 | System prompt assembly   | `prompt_assembly.py`    | Walk ancestors, append guidelines, preserve cache prefix |
| 8 | Lifecycle hooks          | `hooks.py`              | Pre- and post-tool callbacks, trust gate |
| 9 | Shell permission gate    | `tool_registry.py`      | `classify_command` + interactive escalation |

Components 3, 5, and 9 all live in `tool_registry.py` because they share state: the registry is the natural place for both *what* is callable and *whether* a given call is allowed.

## Mapping to the five validation subsystems

`validate_harness.py` does not score modules; it scores *subsystems*. Each of the nine components contributes to one or two subsystems:

| Subsystem      | Primary contributors                                  | What the scorer looks for |
|----------------|-------------------------------------------------------|---------------------------|
| Instructions   | `prompt_assembly.py`, `AGENTS.md`                     | Startup workflow, Definition of Done, routing to state |
| State          | `persistence.py`, `feature_list.json`, `progress.md`  | Append-only log, valid feature schema, restart markers |
| Verification   | `init.sh` / `init.ps1`, `tool_registry.py` (primitives) | Fail-fast, test command, evidence recorded |
| Scope          | `feature_list.json`, `subagent.py`                    | One-feature-at-a-time rule, dependency graph, fork boundary |
| Lifecycle      | `harness.py`, `hooks.py`, `session-handoff.md`        | Bounded loop, hook trust gate, restart story |

## When to extend vs. when to replace

**Extend in place** if the change keeps the contract:
- New tool? Register it in `tool_registry.py`, add a `classify_command` rule if it shells out.
- New telemetry? Add a post-tool hook in `hooks.py`.
- New summarization strategy? Subclass `ContextManager` and inject it into `Harness.__init__`.

**Replace** only if the contract itself changes:
- Multi-step planning that needs more than `run()` can express → write a new orchestrator module and keep `harness.py` as the leaf executor.
- Long-running background tasks → introduce a queue file under `.harness/` and a worker module; do not block the main loop.

## Adapter shape for a real LLM

`harness.py::Harness.run()` ships with a mock turn generator. The integration point is a single method:

```python
def _model_turn(self, messages: list[dict]) -> dict:
    """Return {'role': 'assistant', 'content': str, 'tool_call': dict | None}."""
    ...
```

Provide that method (or override it via a subclass) and everything else — compaction, permission gating, logging — works unchanged. Keep the adapter in the caller's code, not in the harness module, so the harness stays dependency-free.

## Related references

- [Architecture principles](architecture-principles.md) — invariants behind these modules.
- [Tool registry and safety](tool-registry-and-safety.md) — components 3, 5, 9.
- [Context and memory](context-and-memory.md) — components 2, 6, 7.
- [Lifecycle and hooks](lifecycle-and-hooks.md) — components 1, 8.
