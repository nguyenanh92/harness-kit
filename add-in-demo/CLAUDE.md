# Agent Operating Manual — Outlook AI Co-Pilot

Outlook add-in (Office.js + React + TypeScript) dùng Claude API để summarize email thread và generate smart replies.
Dự án này nằm trong `harness-kit/add-in-demo/` và là sản phẩm thật — không phải demo.

## Project Context

- **Stack:** React 18 + TypeScript + Vite + Office.js + Anthropic SDK
- **Target:** Outlook Web + Outlook Desktop (Windows)
- **Phase 1 scope:** Frontend-only, no backend. Claude API gọi trực tiếp từ task pane.
- **API key:** `VITE_ANTHROPIC_API_KEY` trong `.env.local` (không commit)

## Local Dev

```bash
cd add-in-demo/outlook-copilot
npm install
npm run dev          # Vite dev server tại https://localhost:3000
```

Sideload add-in vào Outlook Web: https://outlook.office.com → Settings → Manage add-ins → Upload manifest.

## Startup Workflow

Before writing code, in order:

1. Read this file (`CLAUDE.md`) end-to-end.
2. Open `feature_list.json` — pick feature có `status: "in_progress"`. Nếu không có, promote `pending` đầu tiên.
3. Open `progress.md` — recover `Current State`, `What I Did`, `Recommended Next Step`.
4. Run `./init.ps1` — capture output làm Evidence.

## Stay in Scope

- **One feature at a time.** Không sửa code ngoài feature đang active.
- Dependencies khai báo trong `feature_list.json[].dependencies` — giải quyết theo thứ tự.
- Phát hiện việc của feature khác → append vào `feature_list.json` với `status: "pending"`, không làm ngay.

## Definition of Done

Feature là `done` khi TẤT CẢ đúng:

- `./init.ps1` chạy không lỗi (lint + build pass).
- `feature_list.json` status = `"done"`.
- `progress.md` có Verification Evidence (command + output).
- `session-handoff.md` có Blockers, Files touched, Next Session plan.

## Verification

```powershell
./init.ps1   # npm lint + build, fail fast on error
```

## End of Session

1. Update `progress.md` — `Last Updated`, `Current Objective`, `Recommended Next Step`.
2. Update `session-handoff.md` — `Blockers`, `Files`, `Next Session`.
3. Leave workspace restartable từ `progress.md` + `session-handoff.md` alone.

## Workflow CLI

```bash
py hk.py status                          # xem feature đang active
py hk.py start F-002                     # bắt đầu feature
py hk.py done                            # mark done sau khi init.ps1 pass
py hk.py feature "Tên feature" --desc "" # thêm feature mới
```

## Key Office.js Notes

- Dùng `Office.onReady()` trước mọi Office API call.
- Email body: `Office.context.mailbox.item.body.getAsync("text", cb)`.
- Compose insert: `Office.context.mailbox.item.body.setAsync(text, {coercionType: "text"}, cb)`.
- Office.js không hỗ trợ ES modules trực tiếp — Vite build cần `format: "iife"` cho add-in bundle.

## Security Note

`VITE_ANTHROPIC_API_KEY` lộ ra client bundle ở Phase 1 là chấp nhận được cho evaluation.
Phase 2 sẽ thêm backend proxy để ẩn key.
