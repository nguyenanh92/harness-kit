---
phase: 2
title: "MCP as optional integration layer"
status: pending
priority: P1
effort: "4h"
dependencies: [1]
---

# Phase 2: MCP as optional integration layer

## Overview

Create a new reference doc `mcp-integration.md` that explains MCP as an optional harness extension. Update adjacent docs to acknowledge MCP exists without making it mandatory. The zero-external-deps core invariant stays intact.

## Requirements

- Functional: developers must be able to understand MCP without it being required to use the toolkit
- Non-functional: the "optional" status must be explicit and visible — not buried in caveats

## Architecture

MCP (Model Context Protocol) sits as an **optional layer 4** above the existing 3-tier tool classification:

```
[Your harness core]          ← zero-external-deps (unchanged)
    ↑
[Built-in tools]             ← read_file, write_file, run_shell (unchanged)
    ↑
[MCP servers] (OPTIONAL)     ← external processes, JSON-RPC 2.0, dynamic discovery
    ↑
[Tool registry aggregator]   ← unified dispatch (extended to include MCP namespace)
```

MCP enables:
- **Tools** — dynamic, server-provided, discoverable at runtime
- **Resources** — read-only data sources (files, DB rows, API responses)
- **Prompts** — server-provided prompt templates

## Related Code Files

- Create: `skills/references/mcp-integration.md`
- Modify: `skills/references/tool-registry-and-safety.md` (add MCP section)
- Modify: `skills/references/architecture-principles.md` (update zero-deps constraint with MCP carve-out)
- Modify: `skills/SKILL.md` (mention MCP as optional in capability list)

## Implementation Steps

### 1. Create `skills/references/mcp-integration.md`

Structure:
```
# MCP Integration (Optional)

## What is MCP
## Why it matters (300+ public servers, all major AI providers adopted)
## When to add MCP
## Architecture: how MCP fits the 9-component model
## Transport options (stdio / HTTP+SSE / WebSocket)
## Tool namespace convention: mcp__<server>__<tool>
## Dynamic tool discovery: notifications/tools/list_changed
## Resources and Prompts (two capability types absent from built-in model)
## Adding MCP to a harness — minimal example (JSON-RPC 2.0 only, no SDK required for simple use)
## When to stay stdlib-only
```

Key constraints to document:
- MCP client libraries (`mcp` Python SDK, `@modelcontextprotocol/sdk`) are external dependencies — only add them when opting into MCP
- MCP servers are external processes; harness manages lifecycle (spawn/kill)
- Tool namespace: `mcp__<server-name>__<tool-name>` to avoid collisions with built-ins
- `notifications/tools/list_changed` — tool list is dynamic, not static at startup

### 2. Update `tool-registry-and-safety.md`

Add a "MCP Tools (Optional)" section after the existing tool registry content:
- Explain that `tool_registry.py` can be extended to aggregate MCP tools
- Show how MCP tool names (`mcp__github__get_issue`) differ from built-in names
- Note: MCP tools require the same permission classification as built-in tools
- Reference `mcp-integration.md` for full setup

### 3. Update `architecture-principles.md`

In the "Zero External Dependencies" invariant section:
- Clarify: "Zero external dependencies **in harness/ core modules**"
- Add a carve-out: "Exception: if you opt into MCP integration, the MCP client library is an allowed external dependency — isolated to the MCP adapter module, not imported by harness core"
- This preserves the invariant's intent (reproducibility, portability) while not making MCP impossible

### 4. Update `skills/SKILL.md`

In the capabilities/features list:
- Add "Optional MCP layer: extend tool registry with MCP servers (300+ public servers)"
- Reference `skills/references/mcp-integration.md`

## Success Criteria

- [x] `mcp-integration.md` exists with all 9 sections above
- [x] MCP marked as **optional** in every location it appears (not a requirement)
- [x] `architecture-principles.md` zero-deps invariant updated with explicit MCP carve-out
- [x] `tool-registry-and-safety.md` has MCP section referencing the new doc
- [x] `skills/SKILL.md` mentions MCP as optional feature
- [x] No existing stdlib-only workflow is broken or made to look deprecated

## Risk Assessment

Medium — the "optional" framing must be consistent across all touched files. If any one file presents MCP as the new default, it contradicts the zero-deps invariant and confuses users. Review all edits together before committing.
