---
phase: 2
title: "Custom Reply Context"
status: pending
priority: P1
effort: "~2h"
dependencies: []
---

# Phase 2: Custom Reply Context

## Overview

Let users steer AI-generated replies by typing a short instruction before
hitting "Generate". Examples: "decline politely", "ask for more time",
"agree but suggest Tuesday instead". The instruction is sent to the AI
alongside the email content.

## Requirements

- Functional:
  - Collapsible "Instructions" textarea above the reply cards in the Reply tab
  - Toggle button ("Add context ▾" / "▴") to show/hide the textarea
  - "Regenerate" button replaces the current trigger (auto-generate on mount stays
    as the default first run; user can then customize and regenerate)
  - Instructions field persists in `sessionStorage` so it survives tab switches
    but clears when the add-in is closed
  - Empty instruction → same behavior as today (no extra prompt text)
  - Max ~200 chars; show remaining character count at the edge of the textarea
- Non-functional:
  - `generateReplies` signature change is backward-compatible
    (`context?: string` optional param → existing callers unaffected)
  - No manifest changes; no new dependencies

## Architecture

```
generateReplies(subject, body, context?: string): Promise<ReplyDraft[]>
  — when context is non-empty, append to prompt:
    "Additional instruction from the user: <context>"
  — same dispatch pattern to deepseekReplies

deepseekReplies(subject, body, context?: string): Promise<ReplyDraft[]>

reply-tab.tsx state additions:
  instructions: string          — textarea value, synced to sessionStorage
  showInstructions: boolean     — collapsible toggle
  hasGenerated: boolean         — true after first auto-run; shows Regenerate button
```

### Prompt change (claude-client.ts)

```
// existing tail of the prompt:
"Each reply should be 1-3 sentences. Do not include a subject line."

// append when context is non-empty:
`\nAdditional user instruction: ${context}`
```

## Related Code Files

- Modify: `src/components/reply-tab.tsx` — add instructions state, textarea UI, Regenerate button
- Modify: `src/api/claude-client.ts` — add optional `context` param to `generateReplies`
- Modify: `src/api/deepseek-client.ts` — add optional `context` param to `deepseekReplies`
- Modify: `add-in-demo/feature_list.json` — add F-010

## Implementation Steps

1. **claude-client.ts / deepseek-client.ts**:
   - Add `context?: string` third parameter to `generateReplies` and `deepseekReplies`
   - In the prompt string, append `\nAdditional user instruction: ${context}` only when
     `context?.trim()` is non-empty

2. **reply-tab.tsx** — state:
   ```ts
   const SESSION_KEY = "hk_reply_instructions";
   const [instructions, setInstructions] = useState(
     () => sessionStorage.getItem(SESSION_KEY) ?? ""
   );
   const [showInstructions, setShowInstructions] = useState(false);
   ```
   - On `instructions` change: `sessionStorage.setItem(SESSION_KEY, instructions)`

3. **reply-tab.tsx** — UI layout (insert above the draft cards):
   ```
   [Add context ▾]                 ← toggle button (text-xs, gray)
   ┌──────────────────────────────┐
   │ e.g. "decline politely"      │ ← textarea, 3 rows, shown when expanded
   │                   142 / 200  │ ← char count in bottom-right corner
   └──────────────────────────────┘
   [Regenerate]                    ← primary blue button, full-width
   ```

4. **reply-tab.tsx** — on Regenerate click:
   - Set `loading = true`, clear `drafts`, call `generateReplies(subject, body, instructions.trim())`
   - Same loading skeleton + error handling as current flow

5. **feature_list.json** — append F-010

## Success Criteria

- [x] "Add context" toggle shows/hides the textarea
- [x] Typing in textarea persists after switching away and back to Reply tab
- [x] "Regenerate" with "decline politely" produces visibly different reply cards
- [x] Empty textarea → same output as existing auto-generated replies
- [x] Character counter shows remaining count; input limited to 200 chars
- [x] `npm run build` passes, 0 TypeScript errors

## Risk Assessment

- **Prompt injection** — user-supplied text goes directly into the prompt. Risk is low
  in a personal tool (user is also the attacker), but worth noting. Mitigated by
  keeping context in a clearly labeled section of the prompt, not the system role.
- **Re-generation cost** — each click costs an API call. The textarea makes the action
  deliberate (user must type something), so accidental repeated calls are unlikely.
