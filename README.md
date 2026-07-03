# Command Center + Voice OS

Your empire foundation: a **24/7 voice agent** you call from any phone, and a **command deck portal** you open when you have internet.

## What this is

| Component | Purpose |
|-----------|---------|
| **Voice OS** | Backend that Vapi calls into. Turns your voice commands into tasks, notes, and decisions. |
| **Command Center** | Web portal showing tasks, decisions, voice call history, and activity. |
| **Vapi Integration** | Connects your existing phone number to Voice OS tools. |

## Quick start (local dev)

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p ../data
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
```

### Portal

```bash
cd portal
npm install
npm run dev
```

Open http://localhost:5173 — login with credentials from `.env` (default: `commander` / `change-me`).

## Deploy to VPS (24/7)

```bash
cp .env.example .env
# Edit .env with your domain, passwords, secrets
docker compose up -d
```

- API: port 8000
- Portal: port 3000
- Put HTTPS in front (Caddy/nginx) — required for Vapi

See [docs/VAPI_SETUP.md](docs/VAPI_SETUP.md) for connecting your Vapi number.

## How you use it day-to-day

**At work (no phone, but can call):**
1. Call your Vapi number
2. Tell Voice OS what to build, research, or decide
3. It creates tasks and logs everything

**When you have internet:**
1. Open your Command Center portal
2. See all voice sessions, pending tasks, decisions
3. Make calls on what to approve or prioritize next

## Project structure

```
server/          Voice OS API (FastAPI)
portal/          Command Center web app (React)
docs/            Vapi setup guide + assistant config
docker-compose.yml
```

## Next phases (after foundation)

- Worker agents that execute tasks from the queue
- Email/SMS notifications when decisions need you
- Approval flows for sensitive actions
- CRM and payment integrations

This repo is Phase 1: **voice in, visibility out, always on.**
