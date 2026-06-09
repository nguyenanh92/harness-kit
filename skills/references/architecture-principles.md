# Architecture Principles of a Resilient Agent Harness

This document outlines the core architectural principles that govern the design of a lightweight, highly resilient Agent Harness.

---

## 1. Zero-Dependency & Pure Standard Library

AI Agents operate in diverse environments. Requiring external packages like `langchain`, `langgraph`, or `requests` introduces several critical risks:
- **Dependency bloat**: Increases initial sandbox startup latency.
- **Security vulnerabilities**: Pulling third-party packages dynamically can lead to supply chain attacks.
- **API breakage**: External frameworks change rapidly, breaking older agents.

### The Standard Library Constraint
By using Python's built-in standard library modules exclusively, the harness is guaranteed to work in any basic Python sandbox (version 3.8+):
- `subprocess` / `os` / `sys`: Operating system interactions and shell execution.
- `json` / `pathlib`: Structured configuration and robust, cross-platform file paths.
- `re`: Match patterns and parse shell commands.
- `typing` / `dataclasses`: Strong typing for data structures.

---

## 2. While Loop Centrality

A harness is fundamentally an orchestrator of a single, bounded loop. Every file in the system exists solely to supply resources to or execute actions decided inside this loop.

```
+-------------------------------------------------------------+
|                        WHILE LOOP                           |
|  1. Assemble System Prompt (prompt_assembly.py)             |
|  2. Compact Context if near limit (context_manager.py)      |
|  3. Call LLM (mock / real API)                              |
|  4. Parse tool call from response                           |
|  5. Run Hook -> Pre-tool intercept (hooks.py)               |
|  6. Check Permissions & Safety (tool_registry.py)           |
|  7. Execute Tool & Capture exit code                        |
|  8. Run Hook -> Post-tool audit (hooks.py)                  |
|  9. Append event to Log file (persistence.py)               |
| 10. Repeat until Done or Limit (iteration cap) reached       |
+-------------------------------------------------------------+
```

### Constraints:
- **Iteration Cap**: An agent must never run endlessly. A hard limit (e.g., 30 iterations) must be enforced.
- **Timeout Management**: If a tool hangs (e.g., a test suite waiting for input), it must be terminated after a timeout (e.g., 30 seconds).

---

## 3. Durability via Append-Only Logging

When working on complex, multi-turn tasks, sessions can crash due to network drops, CPU throttling, or terminal terminations. If state is stored in memory, all work is lost.

### Why Append-Only JSON Lines?
- **Immediate flush**: Every event (message, tool call, compaction, user confirmation) is appended to a file (typically `session.jsonl`) and immediately flushed to disk.
- **Replayability**: To resume a session, the harness replays the log line-by-line, reconstructing:
  1. The cumulative context.
  2. The current active feature or task state.
  3. The number of iterations already spent.
- **Concurrency safe**: Two processes sharing a read-only view of the log won't overwrite each other's historical lines.
