# Sideload Guide — Outlook AI Co-Pilot

How to test the add-in locally without publishing to AppSource.

## Prerequisites

- Node.js 18+
- An Outlook account (Microsoft 365 or Outlook.com)
- Browser: Edge or Chrome

## Step 1 — Start the dev server

```powershell
cd add-in-demo/outlook-copilot
npm run dev
```

Server starts at `https://localhost:3000`.
First run: browser will warn about self-signed certificate — click **Advanced → Proceed** to trust it.

## Step 2 — Create `.env.local`

```powershell
Copy-Item .env.local.example .env.local
# Edit .env.local and set your Anthropic API key
```

## Step 3 — Sideload into Outlook Web

1. Open [https://outlook.office.com](https://outlook.office.com)
2. Open any email message
3. Click the **...** (More actions) menu in the email toolbar
4. Select **Get Add-ins**
5. Go to **My add-ins** tab → **Custom add-ins** → **+ Add a custom add-in** → **Add from file...**
6. Upload `add-in-demo/outlook-copilot/manifest.xml`
7. Click **Install** in the warning dialog

## Step 4 — Open the task pane

1. Open any email
2. Click **Open AI Co-Pilot** in the ribbon (or **...** → **AI Co-Pilot**)
3. The task pane opens on the right side

## Icon placeholders

The manifest references icon files at `https://localhost:3000/assets/icon-*.png`.
These are not yet created — Outlook will show a default icon during development.
Add real icons to `outlook-copilot/public/assets/` before publishing.

## Troubleshooting

| Issue | Fix |
|---|---|
| "Add-in manifest is not valid" | Check manifest.xml XML syntax |
| Task pane shows blank page | Open DevTools (F12) and check console errors |
| "Cannot connect to localhost:3000" | Make sure `npm run dev` is running |
| CORS error in console | Anthropic API supports browser CORS — check API key in `.env.local` |
