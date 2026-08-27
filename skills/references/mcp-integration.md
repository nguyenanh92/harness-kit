# MCP Integration (Optional)

Load when you want to extend the tool registry with dynamically discovered tools from external processes.

MCP is optional. The zero-dependency Python harness works fully without it. Add MCP when you need access to ecosystem tools (databases, browsers, APIs, code search) without writing custom tool handlers for each.

## What MCP is

Model Context Protocol is an open standard (JSON-RPC 2.0 over stdio, HTTP+SSE, or WebSocket) that lets external server processes expose tools, resources, and prompts to any compliant client. Adopted by Anthropic, OpenAI, Google, and others; 300+ public servers available as of late 2025.

Three capability types MCP adds that built-in tools do not cover:

| Capability | What it provides |
|------------|-----------------|
| **Tools** | Callable functions, same shape as built-in tools |
| **Resources** | Read-only data sources (files, DB rows, API responses, docs) |
| **Prompts** | Server-provided prompt templates, injectable into system prompt |

## How MCP fits the 9-component model

MCP slots into **component 3 (Tool registry)** as an optional aggregation layer:

```
[harness core]                    ← zero external deps (unchanged)
    ↑
[Built-in tools]                  ← read_file, write_file, run_shell
    ↑
[MCP tool aggregator] (optional)  ← fetches tool lists from MCP servers
    ↑
[Unified tool registry]           ← dispatches by name, regardless of origin
```

The aggregator merges MCP-provided tools into the existing registry. From the harness loop's perspective, a tool named `mcp__github__get_issue` is dispatched identically to `read_file`.

## Tool namespace convention

Prefix all MCP tool names to avoid collisions with built-ins:

```
mcp__<server-name>__<tool-name>
```

Examples:
- `mcp__github__get_issue`
- `mcp__postgres__query`
- `mcp__browser__navigate`

The same scoped-pattern syntax works in allow/deny rules:

```
mcp__github__get_*        # allow all GitHub read tools
mcp__postgres__*          # allow all Postgres tools
```

## Dynamic tool discovery

MCP tool lists are not static. Servers send `notifications/tools/list_changed` when their tool set changes. The aggregator must re-fetch the tool list on this notification rather than caching it at session start.

This is different from built-in tools, which are registered once at startup and never change.

## Transport options

| Transport | When to use |
|-----------|-------------|
| `stdio` | Local processes (safest; no network surface) |
| `HTTP + SSE` | Remote servers or containers |
| `WebSocket` | Bidirectional streaming (browser automation, live feeds) |

For the Python harness, `stdio` is the default. Launch the MCP server as a subprocess and communicate over its stdin/stdout.

## Minimal integration example (stdlib only)

A minimal MCP client needs only `json` and `subprocess` — no SDK required for simple cases:

```python
import json, subprocess, sys

class McpClient:
    def __init__(self, cmd: list[str]):
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        self._id = 0

    def _send(self, method: str, params: dict) -> dict:
        self._id += 1
        msg = json.dumps({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        self.proc.stdin.write((msg + "\n").encode())
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def list_tools(self) -> list[dict]:
        return self._send("tools/list", {})["result"]["tools"]

    def call_tool(self, name: str, arguments: dict) -> dict:
        return self._send("tools/call", {"name": name, "arguments": arguments})["result"]
```

For production use, the official `mcp` Python SDK handles protocol negotiation, error recovery, and transport switching — but adds an external dependency.

## When to add MCP

Add MCP when:
- You need tools the standard library cannot reasonably implement (browser automation, vector search, live API access)
- You want to reuse community servers rather than writing tool handlers
- The harness will run in an environment where external packages are acceptable

Stay stdlib-only when:
- The harness runs in locked-down sandboxes or offline environments
- All required tools can be implemented as thin wrappers around shell commands
- Supply-chain risk is a hard constraint

## Dependencies when opting in

The `mcp` Python SDK (`pip install mcp`) is an external dependency. Isolate it:

```
harness/         ← stdlib only; NEVER import mcp here
harness_mcp/     ← MCP adapter; imports mcp SDK; injected via model_turn pattern
```

The injection pattern (pass a callable to `Harness(model_turn=...)`) keeps the harness module dependency-free even when MCP is active.

## Related references

- [Architecture principles](architecture-principles.md) — zero-deps invariant and the MCP carve-out.
- [Tool registry and safety](tool-registry-and-safety.md) — how MCP tools are classified and dispatched.
- [Nine components](nine-components.md) — where MCP fits in the component model.
