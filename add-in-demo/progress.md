# Progress Log

Single source of truth cho active feature. Append, không rewrite history.

**Last Updated:** 2026-09-08 10:12

## Current Objective

ALL FEATURES DONE — Phase 1 MVP complete.

## Current State

- F-001 DONE: scaffold (Vite + React + TS + Tailwind + Anthropic SDK)
- F-002 DONE: manifest.xml + sideload guide
- F-003 DONE: task pane UI shell (header, tab bar, loading, error states)
- F-004 DONE: Office.js email reader (office-context.tsx, mock fallback)
- F-005 DONE: Thread summarizer (summary-tab.tsx + claude-client.ts summarizeEmail)
- F-006 DONE: Smart reply drafts (reply-tab.tsx — 3 tones, Copy + Insert buttons)

## What I Did

- 2026-08-28 10:00: Scaffold governance files (CLAUDE.md, feature_list.json, init.ps1...)
- 2026-08-28 10:05: Tạo toàn bộ Vite + React + TypeScript project trong `outlook-copilot/`
- 2026-08-28 10:16: `npm install`, `npm run build` pass — F-001 DONE
- 2026-08-28 10:16: F-002 manifest.xml + docs/sideload-guide.md, F-003 UI shell, F-004 office-context.tsx — all done
- 2026-08-28 10:23: Session interrupted. Resume from F-005
- 2026-08-28 10:27: Verify F-005 (summary-tab.tsx already implemented) — init.ps1 pass — DONE
- 2026-08-28 10:28: Implement F-006 reply-tab.tsx (3 tone cards, Copy + Insert) — init.ps1 pass — DONE

## Verification Evidence

```
[init] OK - workspace is clean and restartable

> outlook-copilot@0.1.0 build
> tsc -b && vite build

✓ 76 modules transformed.
dist/index.html                  0.59 kB
dist/assets/index-BBCFPJAN.css   9.13 kB
dist/assets/index-2noRjCJl.js  209.56 kB
✓ built in 1.35s
```

## Recommended Next Step

Phase 1 complete. Để test thật:
1. Tạo `outlook-copilot/.env.local` với `VITE_ANTHROPIC_API_KEY=sk-ant-...`
2. Chạy `npm run dev` trong `outlook-copilot/`
3. Sideload add-in vào Outlook Web theo `docs/sideload-guide.md`
4. Mở email → Summary tab → verify 3 bullets xuất hiện
5. Reply tab → verify 3 tone cards + Copy hoạt động

## Blockers

Cần `VITE_ANTHROPIC_API_KEY` trong `.env.local` trước khi test thật.

## Notes

- **harness-kit finding:** `hk.py done` bị UnicodeEncodeError với `✓` trên Windows cp1252 — feature_list.json vẫn update đúng, chỉ print crash. Fix: set `PYTHONIOENCODING=utf-8` hoặc thay `✓` bằng ASCII trong hk.py.
- tailwind ExperimentalWarning khi build là không đáng kể (node warning, không phải lỗi)
- Insert button chỉ hoạt động trong compose window context (Office.js)
- `@vitejs/plugin-basic-ssl` cung cấp self-signed cert cho HTTPS localhost
