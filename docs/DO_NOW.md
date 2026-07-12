# DO THIS NOW

Physics-limited only. Everything else ships today.

## Next 60 minutes

```bash
# 1. Merge PR #1 on GitHub

# 2. SSH Servury
ssh root@YOUR_VPS_IP
git clone https://github.com/parisschneider10-netizen/Command-center.git
cd Command-center
cp .env.example .env
nano .env   # SECRET_KEY, PORTAL_PASSWORD, PUBLIC_BASE_URL

# 3. Launch
docker compose up -d --build

# 4. Verify
curl http://YOUR_IP:8000/health
```

Open portal: `http://YOUR_IP:3000` — login `commander` / your password.

## Next 30 minutes

1. Vapi dashboard → assistant = `docs/vapi-assistant.json` → webhook `https://YOUR_DOMAIN/vapi/webhook`
2. Cursor → GitHub connected → Cloud secrets → `GH_TOKEN=ghp_...`
3. Call SARA. Say: *"Give me a briefing."*

## Next 2 hours

GitHub Issue:

```markdown
Title: [BUILD] Production HTTPS + expansion live test

@cursor
- Caddyfile from Caddyfile.example
- Test expansion dry run against production API
- Wire n8n webhooks: task-created, agent-queue, expansion-complete
Ship PR. No blockers.
```

## Keys on VPS .env (not in chat)

```env
SERVURY_API_KEY=
GHL_API_KEY=
GHL_COMPANY_ID=
GHL_MTR_RECON_SNAPSHOT_ID=
RENTAHUMAN_API_KEY=
OPENAI_API_KEY=
EXPANSION_DRY_RUN=true
```

Flip `EXPANSION_DRY_RUN=false` after one dry city works.

## Parallel (all at once)

| Track | Action |
|-------|--------|
| **Command** | GitHub Issues + SARA calls |
| **Money** | Lead scraper → `POST /api/value-node/leads` → city-lock |
| **Hire** | RentAHuman bounty: "Deploy docker on Ubuntu VPS" |
| **Document** | `vault/` — log every decision for the world |

## When stuck

GitHub Issue: `@cursor [BLOCKED] <error message>` — paste logs, not keys.

## Success today

- [ ] Health endpoint green
- [ ] SARA call works
- [ ] One GitHub Issue → PR merged
- [ ] One expansion dry run passes
- [ ] Portal shows tasks/leads

No meetings. No planning docs. Ship.
