# Fast Launch Playbook

You chose speed. This is the compressed path. Hire for fires. Ship daily.

## Week 1 — GO LIVE

| Day | Action | Who |
|-----|--------|-----|
| 1 | Merge PR #1, deploy VPS `docker compose up -d` | You or hired DevOps |
| 1 | Connect Vapi + SARA config | You |
| 2 | Domain + HTTPS (Caddy) | Hired help OK |
| 2 | GitHub PAT → `GH_TOKEN` in Cursor | You |
| 3 | First GitHub Issue: `@cursor build X` | You at work |
| 4 | Domain mail OR Migadu bridge → comms API | Agent + hire |
| 5 | Register agents in hive, test claim queue | Agent |
| 7 | **Empire v0.1 live** — call SARA, open portal, GitHub builds | — |

## Week 2 — BUZZ + MONEY

| Action | Who |
|--------|-----|
| Pick value node (lead gen OR micro-API) — skip long decision doc if you already know niche | Commander |
| GitHub Issue: `@cursor scaffold value-node phase 1` | Cloud Agent |
| n8n workflows: task-created, agent-queue, human-escalation | Agent / hire |
| RentAHuman API key — physical overflow | Commander |
| First revenue event logged to treasury | Agent |

## Parallel tracks (don't serialize)

```text
TRACK A — Foundation     TRACK B — Income        TRACK C — Hires
VPS + Voice OS           Value node              RentAHuman
Portal + vault           Comms live              Guardian #1
GitHub command channel   A2A stubs               DevOps freelancer
```

All three run at once. You command via GitHub Issues + SARA.

## GitHub is headquarters

Every build order = **GitHub Issue** with `@cursor` in body.

Example issues to file this week:

1. `[BUILD] Deploy checklist + github actions stub`
2. `[BUILD] Value node: lead capture landing + webhook`
3. `[BUILD] Portal: escalations + treasury tabs`
4. `[DEPLOY] Caddyfile for production domain`
5. `[HIRE] Need human to verify phone/SIP setup` → RentAHuman

## What you still don't skip (30 seconds each)

- `will-manifest.md` — top 3 priorities (can be 3 bullets)
- Wallet daily cap in `.env` — prevents one agent draining you
- Nuclear label on legal/money issues

Everything else: ship, hire, fix live.

## Commander at work

1. **GitHub mobile app** → new Issue → `@cursor ...`
2. **Call SARA** → voice backup → creates task synced to next issue
3. **Review PRs** on break → merge or comment

## Success = 

- [ ] Can call SARA 24/7
- [ ] Can file GitHub Issue → get PR without laptop
- [ ] Portal shows tasks + treasury
- [ ] Value node logging revenue or leads
- [ ] Hired help on retainer for VPS fires

Build the empire at war speed. Structure is already in the repo.
