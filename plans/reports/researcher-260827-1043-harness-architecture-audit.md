# AI Agent Harness Architecture Audit (2025-2026)

**Date:** 2026-08-27
**Sources consulted:** Anthropic Claude Code docs (primary), MCP spec (primary), Agent SDK docs (primary), Anthropic engineering blog (secondary), arxiv preprints 2025-2026 (tertiary), community analysis (tertiary)
**Audit subject:** 9-component harness model documented in harness-kit

---

## Source Credibility

| Source | Weight | Notes |
|--------|--------|-------|
| code.claude.com/docs | High | Anthropic primary docs, verified live Aug 2026 |
| modelcontextprotocol.io/docs | High | MCP spec, current protocol version 2026-07-28 |
| agent-sdk docs (code.claude.com/docs/en/agent-sdk) | High | First-party SDK reference |
| anthropic.com/engineering | High | Anthropic engineering blog |
| arxiv 2025-2026 harness preprints | Medium | Academic, peer-reviewed in progress |
| Medium / Towards AI community posts | Low | Useful signals, not authoritative |

---

## 1. Claude Code's Actual Architecture

**What Anthropic documents:**

Claude Code is explicitly framed as an **"agentic harness"** around the LLM — this exact term appears in the official docs: *"Claude Code serves as the agentic harness around Claude: it provides the tools, context management, and execution environment that turn a language model into a capable coding agent."*

The formula **LLM (engine) + Harness = AI Agent** is **confirmed as Anthropic's own framing.**

The agentic loop has three phases (gather context, take action, verify results), all blending together. Sessions persist as plaintext **JSONL** under `~/.claude/projects/`, written turn-by-turn — this confirms the append-only JSONL pattern.

The extensibility model now has **six distinct layers** (not present in the 9-component model):
1. Built-in tools (File, Search, Execution, Web, Code Intelligence, Orchestration)
2. MCP servers (external services)
3. Skills (packaged domain workflows, load on demand)
4. Hooks (lifecycle shell/HTTP/agent/prompt callbacks)
5. Sub-agents / Agent SDK (programmable orchestration)
6. Plugins (bundles of skills + hooks + MCP servers + agents)

Timeline of extension additions: MCP (Nov 2024), Subagents (Jul 2025), Hooks (Sep 2025), Skills + Plugins (Oct 2025), Agent Teams (Feb 2026), Agent SDK GA (2026), dynamic workflows/parallel orchestration (May 2026).

---

## 2. Component-by-Component Verdict

### While Loop
**Status: Confirmed, but formalized**

The loop is documented precisely as: receive prompt → evaluate → tool calls → execute tools → repeat until text-only response. Now formally called an "agent loop" with `max_turns` and `max_budget_usd` controls. The loop is embeddable via Agent SDK (`query()` function in Python/TypeScript).

**Gap in current docs:** Current docs likely don't expose `max_turns`, `max_budget_usd`, or `effort` levels (low/medium/high/xhigh/max) as loop controls.

### Context Management
**Status: Significantly evolved**

The 9-component model describes context management as a generic concern. What Claude Code 2026 actually does:

- System prompt + CLAUDE.md + tool definitions + conversation history all accumulate in one window
- **Prompt caching** is automatic for stable prefixes (system prompt, CLAUDE.md, tool schemas) — this is a major cost/latency optimization not present in the original model
- MCP tool schemas are **deferred by default** via "tool search" — only tool names load at session start, full schemas load on-demand
- Skills load summaries at start; full content only on invocation
- Path-scoped `.claude/rules/*.md` load only when matching files are read
- Subagent context windows are fully isolated (no parent history unless fork)

**Gap in current docs:** Prompt caching, lazy tool schema loading, path-scoped rules.

### Tools/Skills Registry
**Status: Split and superseded**

The monolithic "tools/skills registry" concept is now three distinct mechanisms:

1. **Built-in tools** — hardcoded set (Read, Edit, Write, Glob, Grep, Bash, WebSearch, WebFetch, Agent, Skill, TaskCreate, TaskUpdate, etc.)
2. **MCP servers** — external tool providers via JSON-RPC 2.0 protocol; the harness aggregates tools from all connected servers into a unified registry presented to the LLM. MCP is now the industry standard (OpenAI, Google, Anthropic all adopted it). 300+ public MCP servers as of Dec 2025.
3. **Skills** — markdown files with frontmatter; inject instructions or workflow steps on invocation, not external processes

**MCP critically changes the registry model:** Tools are no longer static. MCP servers can notify the host when the tool list changes (`notifications/tools/list_changed`), making the tool registry dynamic. MCP also supports Resources (data context) and Prompts (templates) — two capability types the 9-component model doesn't have.

**Gap in current docs:** MCP's role as a dynamic, federated tool registry. Distinction between Skills (instruction injection) and MCP tools (executable external functions).

### Sub-Agent Management
**Status: Dramatically expanded — single-level restriction is WRONG**

The "single-level sub-agent fork restriction" claim is **incorrect** per current Claude Code docs:

- Default depth limit: **3 layers** below the main conversation (not 1)
- Configurable via `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
- Concurrent limit: **20 subagents** simultaneously (configurable via `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`)
- **Forks** are a distinct type: inherit full conversation history, run same model as parent, share prompt cache with parent, **cannot spawn further forks** (forks are single-level, regular subagents are not)
- Background vs. foreground subagents with different tool sets
- Chained, parallel, and session-resumable subagent patterns
- `SendMessage` tool enables peer-to-peer subagent communication

The Agent SDK further supports `AgentDefinition` with per-agent `permissionMode`, `effort`, `tools`, `model`, and `memory` fields.

**Anthropic's multi-agent research system** uses orchestrator-worker with a lead agent (Opus 4) spawning 3-5 parallel worker subagents (Sonnet 4), achieving 90.2% improvement over single-agent for breadth-first research.

**Gap in current docs:** Single-level restriction is factually wrong. Concurrent limits, fork vs. subagent distinction, `SendMessage` for peer comms.

### Built-in Skills
**Status: Confirmed but renamed/restructured**

Built-in tool categories match the model. Skills are now a separate mechanism from tools — they're markdown-based instruction packages invoked by name (`/skill-name`), not executable functions. Skills can have frontmatter-defined hooks, tools allowlists, and even spawn subagents.

### Session Persistence / Memory
**Status: Confirmed on persistence; significantly evolved on memory**

**Session persistence:** JSONL append-only confirmed. Files live at `~/.claude/projects/<project>/`, organized by git repo. Transcripts auto-deleted after `cleanupPeriodDays`. Sessions are resumable, forkable, and (via Agent SDK) storable to remote backends.

**Memory — major evolution:** Two distinct memory systems now exist:

1. **CLAUDE.md** (human-authored): Scoped at managed policy / user / project / local levels. Supports `@path` imports, path-scoped `.claude/rules/` files, and org-wide deployment. Loaded every session. Multiple files concatenated in order from root to working directory.

2. **Auto memory** (Claude-authored): Stored as structured markdown files at `~/.claude/projects/<project>/memory/`. `MEMORY.md` index (first 200 lines / 25KB loaded at session start). Per-entry topic files loaded on demand. Four typed categories: `user`, `feedback`, `project`, `reference`. Claude decides what's worth remembering. Shared across worktrees. Subagents can have their own auto memory.

**The "append-only JSONL + markdown handoff" pattern is accurate but incomplete.** Production systems now have a structured, queryable auto memory layer on top of raw JSONL transcripts.

**Gap in current docs:** Auto memory system with typed entries, MEMORY.md index pattern, per-subagent memory, remote session storage backends.

### System Prompt Assembly
**Status: More complex than described**

Assembly order (from official docs):
1. System prompt core (hardcoded)
2. Managed policy CLAUDE.md
3. User-level CLAUDE.md (`~/.claude/CLAUDE.md`)
4. Project CLAUDE.md (root-to-cwd, concatenated)
5. CLAUDE.local.md files
6. Path-scoped `.claude/rules/*.md` (loaded on demand)
7. Auto memory MEMORY.md (first 200 lines)
8. Tool definitions (built-in; MCP schemas deferred)
9. Skill descriptions (summaries only)

CLAUDE.md content is injected as a **user message** (not system prompt). Only `--append-system-prompt` CLI flag adds to the actual system prompt. The memory layer re-injects after compaction.

**Gap in current docs:** The injection as user message (not system prompt), the layered CLAUDE.md resolution order, and the post-compaction re-injection behavior.

### Lifecycle Hooks
**Status: Massively expanded — all-or-nothing trust is WRONG**

The original "all-or-nothing hook trust" model is **incorrect**. Claude Code 2026 has a 5-type, 7-scope, multi-event hook system:

**Hook types:** command, http, mcp_tool, prompt, agent (5 types, not 1)

**Hook events (blocking-capable):** `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PostToolUse`, `Stop`, `StopFailure`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `ConfigChange`, `PostToolBatch`, `Elicitation`, `ElicitationResult`, `PreCompact`, `FileChanged`, `CwdChanged`, `DirectoryAdded`, `InstructionsLoaded`

**Exit code contract:** Only exit code `2` blocks. Exit 0 = proceed normally. Exit 1/3-N = non-blocking error.

**Trust model (7 scopes, not all-or-nothing):**
| Scope | Trust |
|-------|-------|
| Managed policy settings | Admin-controlled, always runs |
| User `~/.claude/settings.json` | User-trusted, all projects |
| Project `.claude/settings.json` | Requires workspace trust dialog |
| Project `.claude/settings.local.json` | Workspace trust |
| Plugin `hooks/hooks.json` | Plugin trust level |
| Skill/Subagent frontmatter | Workspace trust for project files |
| `allowManagedHooksOnly` (enterprise) | Blocks all non-managed hooks |

Hooks run outside the context window (no token cost). HTTP hooks support `Authorization` headers with `allowedEnvVars`. Agent hooks can spawn their own subagents.

**Gap in current docs:** Completely wrong trust model. Missing 4 of 5 hook types. Missing `PreCompact` hook for transcript archiving before compaction.

### Permissions / Safety
**Status: Expanded from 3 levels to 6 modes with fine-grained rules**

The original 3-tier model (READ_ONLY / WORKSPACE_WRITE / FULL_ACCESS) has been replaced by:

**6 permission modes:**
1. `default` — unmatched tools → `canUseTool` callback
2. `acceptEdits` — auto-approves file edits + common filesystem ops
3. `plan` — read-only exploration; file edits never auto-approved
4. `dontAsk` — anything not pre-approved is denied (no prompting)
5. `auto` — model classifier reviews most actions
6. `bypassPermissions` — full access except critical paths and explicit deny rules

**Evaluation order (6 steps, not fail-closed binary):**
1. Hooks (can deny)
2. Deny rules (`disallowed_tools`)
3. Ask rules (route to callback)
4. Permission mode
5. Allow rules (`allowed_tools`)
6. `canUseTool` callback

Critical-path protections (`rm`/`rmdir` on system paths) apply in **all modes** including `bypassPermissions`.

Declarative rules support scoped patterns: `Bash(rm *)`, `Edit(//secrets/**)`, `mcp__github__get_*`.

**Gap in current docs:** 3-tier model is outdated. Missing `auto` mode (classifier-based), `plan` mode, `dontAsk` mode, 6-step evaluation order, scoped tool rules.

### Token Compaction at 80% Threshold
**Status: Threshold is WRONG; strategy has evolved**

Official sources contradict the 80% threshold:
- Auto-compaction triggers at approximately **90-95%** of the context window (source: Claude Code docs + `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` env var)
- Default around **95%** for a 200K window ≈ ~190K tokens before compaction
- Reserved buffer for response: ~33K tokens (16.5% of 200K) as of early 2026

**Compaction process:**
1. Clears older tool outputs first
2. Generates condensed narrative (goals, decisions, files touched, current state)
3. Replaces full history with summary as synthetic message
4. CLAUDE.md is re-injected from disk after compaction
5. `PreCompact` hook fires before compaction (allows transcript archiving)
6. `compact_boundary` event emitted in SDK stream after compaction
7. Manual compaction: `/compact [focus]` command

Compaction instructions can be embedded in CLAUDE.md to guide what the compactor preserves.

**Gap in current docs:** 80% threshold is wrong. Missing `PreCompact` hook, `compact_boundary` event, custom compaction instructions, re-injection of CLAUDE.md post-compaction.

---

## 3. What's Confirmed Accurate

- **LLM + Harness = AI Agent** formula — Anthropic uses this exact framing
- **While Loop** as the core mechanism — confirmed, now called "agent loop"
- **Append-only JSONL** for session persistence — confirmed at `~/.claude/projects/`
- **System Prompt Assembly** as a component — confirmed, more layers now
- **Fail-closed permission gate** — directionally correct, now more granular
- **Context Management** as a component — confirmed, now more sophisticated
- **Sub-Agent Management** as a component — confirmed, massively expanded

---

## 4. What's Missing from the 9-Component Model

These are architecturally significant components not in the original 9:

| Missing Component | Why It Matters |
|-------------------|----------------|
| **MCP (Model Context Protocol)** | Now the standard for tool federation; replaces ad-hoc tool registries; 300+ servers; dynamic tool discovery with notifications; Tools + Resources + Prompts primitives |
| **Plugins** | Bundle packaging unit for skills + hooks + MCP + agents; organizational distribution mechanism |
| **Auto Memory system** | Structured, typed, queryable memory layer on top of JSONL (MEMORY.md index + topic files) |
| **Prompt Caching** | Major cost/latency component; automatic for stable prefixes; affects architecture decisions |
| **Session Storage adapters** | Remote session persistence for stateless/serverless deployments |
| **Effort / Reasoning Control** | 5 levels (low/medium/high/xhigh/max) per agent or per subagent; architectural trade-off control |
| **Agent SDK** | Harness-as-library; embeds the same loop in custom applications (Python/TypeScript) |
| **Checkpoint / Rewind** | File snapshot before edits; separate from git; rollback without session restart |

---

## 5. Trade-Off Assessment of Current 9-Component Model

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Conceptual accuracy | Good | Core formula and loop structure correct |
| Component completeness | Poor | Missing MCP, auto memory, plugins, effort, caching |
| Permission model accuracy | Poor | 3-tier vs. 6-mode; wrong evaluation order |
| Subagent accuracy | Poor | Single-level restriction factually wrong (3 levels default) |
| Hook model accuracy | Poor | All-or-nothing vs. 7-scope trust; missing 4 hook types |
| Compaction threshold | Poor | 80% vs. ~95%; missing PreCompact hook and re-injection |
| Memory model | Partial | JSONL confirmed; auto memory layer missing |
| MCP coverage | None | Entirely absent; now a core architectural component |

---

## 6. Adoption Risk for Harness Implementations That Follow the 9-Component Model

- **High risk:** Implementing single-level subagent restriction will break against Claude Code's actual 3-level default; any integration will behave differently from reference
- **High risk:** Implementing all-or-nothing hook trust misses workspace trust scoping; security boundaries will be wrong
- **Medium risk:** 80% compaction threshold creates premature compaction vs. Claude Code behavior
- **Medium risk:** 3-tier permission model will confuse users familiar with `plan`/`auto`/`dontAsk` modes
- **Low risk:** Core loop structure, JSONL persistence, and LLM+harness formula are durable

---

## 7. Limitations of This Research

- Did not audit the harness-kit codebase itself against these findings — only compared doc claims to Anthropic's live documentation
- MCP server security research (injection attacks, `_meta` poisoning) was found but not synthesized — relevant if harness-kit handles untrusted MCP servers
- Managed Agents (hosted REST API product) not researched — separate product from Claude Code but uses same loop primitives
- `auto` permission mode (classifier-based) behavior not deeply investigated — availability varies by plan

---

## Unresolved Questions

1. Does harness-kit implement its own compaction, or does it delegate to Claude Code? If own: the 80% threshold needs correction and the PreCompact hook integration should be added.
2. What is the harness-kit's current stance on MCP — is it planned, deferred, or out of scope? MCP is now load-bearing for production agent deployments.
3. Does the "single-level fork restriction" refer to forks specifically (which are still single-level in Claude Code) or regular subagents? If the former, it's correct for forks but wrong as a general subagent statement.
4. Is the zero-external-dependencies (stdlib Python only) constraint still a design goal? MCP integration and the Agent SDK both require external packages.

---

## Sources

- [Claude Code Overview](https://code.claude.com/docs/en/overview)
- [How Claude Code Works](https://code.claude.com/docs/en/how-claude-code-works)
- [Claude Code Memory / CLAUDE.md](https://code.claude.com/docs/en/memory)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code Sub-Agents](https://code.claude.com/docs/en/sub-agents)
- [Agent SDK Overview](https://code.claude.com/docs/en/agent-sdk/overview)
- [Agent SDK: Agent Loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)
- [Agent SDK: Permissions](https://code.claude.com/docs/en/agent-sdk/permissions)
- [MCP Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [Anthropic: Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic: A Harness for Every Task](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code)
- [Anthropic: Getting Started with Loops](https://claude.com/blog/getting-started-with-loops)
- [Multi-Agent Orchestration Patterns 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
- [State of AI Agent Memory 2026 (Mem0)](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Claude Code Context Compaction](https://amux.io/guides/claude-code-context-compaction/)
