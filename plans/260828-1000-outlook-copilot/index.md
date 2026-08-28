# Plan: Outlook AI Co-Pilot Add-in

**Date:** 2026-08-28
**Branch:** main
**Root:** `harness-kit/add-in-demo/`
**Status:** READY — F-001 next

## Outcome

Xây dựng Outlook task pane add-in dùng Claude API để:
1. Tóm tắt email thread thành 3 bullet points + action items
2. Sinh 3 smart reply drafts với 3 tones khác nhau

Mục tiêu kép: sản phẩm thật + đánh giá harness-kit workflow trong thực tế.

## Constraints

- Phase 1: Frontend-only (không BE, không auth)
- API key lộ ra client là chấp nhận được ở phase này
- Target: Outlook Web + Outlook Desktop (Windows)
- Nằm trong `harness-kit/` repo, không tách repo riêng

## Non-goals (Phase 1)

- Backend proxy
- Microsoft AppSource publish
- Follow-up reminder (Phase 2)
- Auth / multi-user

## Tech Stack

| Layer | Choice | Lý do |
|---|---|---|
| Framework | React 18 + TypeScript | Office.js ecosystem chuẩn |
| Build | Vite (iife output) | Nhanh, config flexible cho Office bundle |
| Styling | Tailwind CSS | Rapid UI, blend với Outlook theme |
| AI | `@anthropic-ai/sdk` | Gọi trực tiếp từ task pane |
| Add-in | `@microsoft/office-js` | Official Office.js types |
| Dev cert | `office-addin-dev-certs` | HTTPS local cho sideloading |

## Features & Phases

### Phase 1 — MVP (hiện tại)

| ID | Feature | Depends | Status |
|---|---|---|---|
| F-001 | Project scaffold (Vite + React + TS) | — | pending |
| F-002 | Outlook manifest & sideload | F-001 | pending |
| F-003 | Task pane UI shell | F-001 | pending |
| F-004 | Email content reader (Office.js) | F-002, F-003 | pending |
| F-005 | Thread summarizer (Claude API) | F-004 | pending |
| F-006 | Smart reply drafts (Claude API) | F-004 | pending |

**Sequence:**
```
F-001 → F-002 ──┐
      → F-003 ──┴→ F-004 → F-005
                         → F-006
```

### Phase 2 — (sau khi Phase 1 hoàn thành)

- Backend proxy (Node.js + Fastify) ẩn API key
- Follow-up reminder (client-side localStorage)
- Microsoft AppSource submission

## File Structure (target)

```
add-in-demo/
├── CLAUDE.md
├── feature_list.json
├── progress.md
├── session-handoff.md
├── hk.py
├── init.ps1
└── outlook-copilot/
    ├── manifest.xml
    ├── .env.local              # VITE_ANTHROPIC_API_KEY (gitignored)
    ├── vite.config.ts
    ├── package.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── app.tsx
        ├── office-context.tsx  # Office.onReady wrapper + mailbox reader
        ├── api/
        │   └── claude-client.ts
        ├── components/
        │   ├── tab-bar.tsx
        │   ├── summary-tab.tsx
        │   └── reply-tab.tsx
        └── styles/
            └── tailwind.css
```

## Acceptance Criteria

- [ ] `./init.ps1` pass (lint + build không lỗi)
- [ ] Add-in load được trong Outlook Web (sideloaded)
- [ ] Click email → Summary tab hiện 3 bullets trong < 5 giây
- [ ] Reply tab sinh 3 drafts, nút Copy hoạt động
- [ ] Không có console error liên quan Office.js

## Harness-kit Evaluation Checkpoints

Sau mỗi feature, ghi nhận vào `progress.md`:
- hk.py có giúp track được không?
- CLAUDE.md có đủ context để agent tiếp tục không?
- init.ps1 có bắt được lỗi thật không?

## Risks

| Rủi ro | Mitigation |
|---|---|
| Vite iife build conflict với Office.js globals | Test build sớm ở F-001, xem `office-js-helpers` |
| Office.js API khác nhau giữa Web và Desktop | Test Outlook Web trước, Desktop sau |
| CORS khi gọi Anthropic API từ browser | Anthropic API hỗ trợ browser CORS — OK |
