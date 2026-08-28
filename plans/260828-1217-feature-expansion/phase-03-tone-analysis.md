---
phase: 3
title: "Tone Analysis Badge"
status: pending
priority: P2
effort: "~1.5h"
dependencies: []
---

# Phase 3: Tone Analysis Badge

## Overview

Extend the Summary tab to show a small tone badge beside the "Key Points"
heading: **Urgent**, **Formal**, **Friendly**, or **Neutral**. The tone is
detected by the same AI call that generates the summary, so there is no
extra API request — only a prompt and schema change.

## Requirements

- Functional:
  - `SummaryResult` gains a `tone` field: `"urgent" | "formal" | "friendly" | "neutral"`
  - AI prompt instructs the model to include `"tone"` in its JSON response
  - Summary tab renders a colored pill badge next to "Key Points" heading
  - Badge colors:
    - `urgent` → red (`bg-red-100 text-red-700`)
    - `formal` → blue (`bg-blue-100 text-blue-700`)
    - `friendly` → green (`bg-emerald-100 text-emerald-700`)
    - `neutral` → gray (`bg-gray-100 text-gray-600`)
  - If `tone` is missing or unrecognized (defensive), badge is hidden
- Non-functional:
  - Single prompt change; no new API call, no new dependency
  - Both Anthropic and DeepSeek providers must return `tone`
  - Backward-compatible: if old cached data lacks `tone`, UI degrades gracefully

## Architecture

```
SummaryResult (claude-client.ts):
  before: { bullets: string[]; actionItems: string[] }
  after:  { bullets: string[]; actionItems: string[]; tone?: "urgent"|"formal"|"friendly"|"neutral" }

Prompt change — add to JSON schema instruction:
  "tone": "one of: urgent, formal, friendly, neutral"

summary-tab.tsx — ToneBadge component:
  const TONE_STYLE = {
    urgent:   "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
    formal:   "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
    friendly: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
    neutral:  "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300",
  };
  const TONE_LABEL = { urgent:"Urgent", formal:"Formal", friendly:"Friendly", neutral:"Neutral" };
```

## Related Code Files

- Modify: `src/api/claude-client.ts` — extend `SummaryResult`, update `summarizeEmail` prompt
- Modify: `src/api/deepseek-client.ts` — update `deepseekSummarize` prompt to match
- Modify: `src/components/summary-tab.tsx` — add `ToneBadge` component, render beside heading
- Modify: `add-in-demo/feature_list.json` — add F-011

## Implementation Steps

1. **claude-client.ts** — update `SummaryResult` and prompt:
   ```ts
   export interface SummaryResult {
     bullets: string[];
     actionItems: string[];
     tone?: "urgent" | "formal" | "friendly" | "neutral";
   }
   ```
   Prompt JSON schema becomes:
   ```
   {
     "bullets": ["key point 1", ...],
     "actionItems": ["action 1", ...],
     "tone": "urgent | formal | friendly | neutral"
   }
   ```

2. **deepseek-client.ts** — same prompt and return-type update for `deepseekSummarize`

3. **summary-tab.tsx** — add `ToneBadge`:
   ```tsx
   function ToneBadge({ tone }: { tone?: SummaryResult["tone"] }) {
     if (!tone || !TONE_STYLE[tone]) return null;
     return (
       <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${TONE_STYLE[tone]}`}>
         {TONE_LABEL[tone]}
       </span>
     );
   }
   ```
   Place it in the "Key Points" heading row:
   ```tsx
   <h2 className="flex items-center gap-2 ...">
     <DocumentIcon /> Key Points <ToneBadge tone={result.tone} />
   </h2>
   ```

4. **feature_list.json** — append F-011

## Success Criteria

- [x] Summary tab shows a tone badge when AI returns a valid tone value
- [x] Each of the 4 tone values renders with the correct color
- [x] Badge is absent (no blank space) when `tone` is undefined or unrecognized
- [x] Dark mode colors display correctly
- [x] `npm run build` passes, 0 TypeScript errors
- [x] No regression in existing bullet/action-item rendering

## Risk Assessment

- **Model compliance** — AI may ignore the new field or return an unexpected value.
  Mitigated by defensive rendering (`if (!tone || !TONE_STYLE[tone]) return null`).
  Observable signal: badge never appears. Pre-decided response: tighten prompt wording
  (e.g., add `"IMPORTANT: tone must be exactly one of the four values listed"`).
- **JSON parse failure** — if model wraps response in markdown fences despite instruction,
  existing `JSON.parse(text)` will throw. Already a pre-existing risk; no new exposure.
