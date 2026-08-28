---
phase: 1
title: "Translate Tab"
status: pending
priority: P1
effort: "~2h"
dependencies: []
---

# Phase 1: Translate Tab

## Overview

Add a 4th tab "Translate" that lets the user convert the current email body
between Vietnamese and English with a single button click. Output is shown
inline with a Copy button.

## Requirements

- Functional:
  - Two action buttons: "→ Tiếng Việt" and "→ English"
  - Calls AI with the full email body + target language instruction
  - Displays translated text below the buttons
  - Copy button copies translated text to clipboard
  - Loading skeleton while waiting for AI response
  - Error state with message on failure
- Non-functional:
  - Works with both Anthropic and DeepSeek providers via existing key-store
  - No manifest changes required (tab is inside the existing task pane)
  - Build must stay 0 TypeScript errors

## Architecture

```
Tab type: "summary" | "reply" | "settings" | "translate"

New function signatures:
  claude-client.ts:   translateEmail(body: string, target: "vi" | "en"): Promise<string>
  deepseek-client.ts: deepseekTranslate(body: string, target: "vi" | "en"): Promise<string>

Routing: claude-client.translateEmail dispatches to deepseekTranslate when
  provider === "deepseek", same pattern as summarizeEmail/generateReplies.

New component: src/components/translate-tab.tsx
  - reads email from useEmail() hook (already available)
  - local state: result (string|null), loading, error, activeLang ("vi"|"en"|null)
```

## Related Code Files

- Create: `src/components/translate-tab.tsx`
- Modify: `src/app.tsx` — import TranslateTab, add "translate" to Tab union, route activeTab
- Modify: `src/components/tab-bar.tsx` — add globe icon + "Translate" entry to TABS array
- Modify: `src/api/claude-client.ts` — add `translateEmail` function
- Modify: `src/api/deepseek-client.ts` — add `deepseekTranslate` function
- Modify: `add-in-demo/feature_list.json` — add F-009

## Implementation Steps

1. **claude-client.ts** — add `translateEmail(body, target)`:
   - Dispatches to `deepseekTranslate` when provider is deepseek
   - Prompt: `"Translate the following email body to ${target === 'vi' ? 'Vietnamese' : 'English'}. Return only the translated text, no explanation."`
   - Returns raw string (no JSON parsing needed)

2. **deepseek-client.ts** — add `deepseekTranslate(body, target)`:
   - Same prompt pattern, fetch to DeepSeek chat completions endpoint
   - Return `data.choices[0].message.content`

3. **translate-tab.tsx** — new component:
   - Show two buttons: "→ Tiếng Việt" / "→ English"
   - On click: set `activeLang`, call `translateEmail`, show loading skeleton then result
   - Skeleton: 4 lines of varying widths, `animate-pulse`
   - Result card: white/dark bg, translated text, CopyButton (reuse pattern from reply-tab)
   - Active button highlighted in outlook blue; other button neutral

4. **tab-bar.tsx** — add 4th tab entry:
   - Icon: globe SVG (`M12 21a9.004 9.004 0 008.716-6.747M12 21...` heroicon globe)
   - Label: "Translate"

5. **app.tsx** — extend Tab type, add TranslateTab route in `<main>`

6. **feature_list.json** — append F-009 with status "done" after implementation

## Success Criteria

- [x] "Translate" tab renders as 4th tab with globe icon
- [x] "→ Tiếng Việt" button translates an English email to Vietnamese
- [x] "→ English" button translates a Vietnamese email to English
- [x] Loading skeleton shows while AI is processing
- [x] Copy button copies translated text; shows "Copied" confirmation
- [x] Error banner shows on AI failure
- [x] `npm run build` passes, 0 TypeScript errors

## Risk Assessment

- **DeepSeek translation quality** — DeepSeek is generally good at Vietnamese, but CORS
  may still block browser requests. Already warned in Settings tab; no new mitigation needed.
- **Long emails** — AI may truncate. Mitigated by using `max_tokens: 1024` to give headroom.
  Observable signal: translated text cuts mid-sentence. Pre-decided response: increase max_tokens
  or truncate email body at 3000 chars with a notice.
