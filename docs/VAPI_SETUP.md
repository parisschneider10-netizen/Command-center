# Vapi Setup Guide

Connect your existing Vapi phone number to the Voice OS backend.

## Architecture

```
You (phone call) → Vapi → Voice OS API (your VPS) → Command Center DB
                              ↓
                    Command Center Portal (browser)
```

When you call your Vapi number, the assistant uses **tools** that hit your server. Everything gets logged so you can see it in the portal when you have internet.

## Step 1: Deploy to your VPS

1. Copy this repo to your Servury VPS
2. Copy `.env.example` to `.env` and fill in values
3. Set `PUBLIC_BASE_URL` to your VPS domain (must be HTTPS for Vapi)
4. Run: `docker compose up -d`
5. Verify: `curl https://your-domain.com/health`

## Step 2: Configure Vapi Assistant

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai)
2. Create or edit your assistant
3. Use `docs/vapi-assistant.json` as a template
4. Replace `YOUR-VPS-DOMAIN.com` with your actual domain in:
   - `serverUrl` → `https://your-domain.com/vapi/webhook`
   - Each tool `server.url` → `https://your-domain.com/voice/tools/...`
5. Attach your existing phone number to this assistant

## Step 3: Test the voice loop

Call your Vapi number and say:

> "Give me a briefing."

> "Create a task: set up my business website landing page. Priority high."

> "Log a note: research competitor pricing this weekend."

Hang up, then log into your Command Center portal and confirm tasks and activity appear.

## Voice OS Tools Reference

| Tool | What it does |
|------|-------------|
| `create_task` | Queues work — builds, research, follow-ups |
| `get_briefing` | Reads back your empire status |
| `queue_decision` | Saves a decision for portal review |
| `update_task` | Marks tasks in progress / done |
| `log_note` | Captures ideas to the activity feed |

## HTTPS Requirement

Vapi requires a public HTTPS URL for webhooks and tool calls. Options:

- **Caddy** (easiest) — auto SSL with a domain pointed at your VPS
- **Cloudflare Tunnel** — free HTTPS without opening ports
- **nginx + Let's Encrypt** — manual cert setup

## Troubleshooting

**Calls work but tools fail:** Check that `PUBLIC_BASE_URL` matches your HTTPS domain and ports 443 is open.

**Portal empty after calls:** Confirm webhook URL is set in Vapi and `/vapi/webhook` returns `{"ok": true}`.

**Can't log into portal:** Default credentials are in `.env` (`PORTAL_USERNAME` / `PORTAL_PASSWORD`). Change these before going live.
