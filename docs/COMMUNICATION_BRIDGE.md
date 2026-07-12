# Communication Bridge — Talk to the Hive Before & After Command Deck

You need to **command the build** from work, then **run the money plays** once the deck is online. This doc is the map.

## Short answer: Do NOT connect Gmail to Cursor

| ❌ Don't | ✅ Do instead |
|----------|---------------|
| Give Cursor your Gmail password | GitHub Issue → `@cursor` |
| OAuth Gmail into the agent | Call SARA (Vapi) |
| Paste API keys in chat | Sovereign mail → `[BUILD]` email commands |
| Expect me to read your inbox directly | Forward Gmail → `commander@yourdomain.com` |

**Gmail is a bridge, not the destination.** Forward to sovereign mail or use GitHub email-to-issue. Agents read **your** comms API — not Google's API tied to Cursor.

---

## The three bridges (use all three)

```text
┌─────────────────────────────────────────────────────────────┐
│                    YOU (at work, phone)                      │
└────────────┬────────────────────┬───────────────────────────┘
             │                    │
    ┌────────▼────────┐   ┌───────▼────────┐   ┌──────────────▼──────────┐
    │ GITHUB ISSUES   │   │  VOICE (SARA)  │   │  EMAIL COMMANDS         │
    │ @cursor builds  │   │  Vapi hotline  │   │  [BUILD] subject lines  │
    │ Works NOW       │   │  Needs VPS     │   │  Needs sovereign mail     │
    └────────┬────────┘   └───────┬────────┘   └──────────────┬──────────┘
             │                    │                            │
             └────────────────────┼────────────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │   COMMAND CENTER API    │
                    │   tasks · vault · n8n   │
                    └────────────┬────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │  CURSOR CLOUD AGENT     │
                    │  builds PRs on GitHub   │
                    └─────────────────────────┘
```

### Bridge 1 — GitHub Issues (PRIMARY, works today)

**No VPS required.** Open GitHub on your phone:

```markdown
Title: [BUILD] Deploy command deck on Servury VPS

Body:
@cursor

Deploy docker compose, Caddy HTTPS, wire Vapi webhook.
Branch: cursor/deploy-command-deck-1894
```

See [GITHUB_COMMAND.md](GITHUB_COMMAND.md).

**GitHub email shortcut:** Repo → Settings → enable email for issues. Email your repo's issues address with `@cursor` in the body.

### Bridge 2 — Voice / SARA (hotline)

Once VPS is live + Vapi webhook set:

| Say | Result |
|-----|--------|
| *"Create task: wire laundry GHL form"* | Task + agent queue |
| *"Issue will: deploy treasury tab, priority 9"* | Urgent agent task |
| *"Dump to vault: KC host pitch v2"* | Obsidian inbox |
| *"Acquisition briefing"* | What you can afford |
| *"Nuclear: approve $500 Starlink"* | Commander queue only |

See [VAPI_SETUP.md](VAPI_SETUP.md).

### Bridge 3 — Email commands (sovereign mail)

**Not Gmail-to-Cursor.** Setup:

1. Get `commander@yourdomain.com` (Migadu $19/yr or self-hosted Stalwart)
2. Add to VPS `.env`: `COMMS_IMAP_*`, `COMMS_SMTP_*`
3. Add your personal email: `BRIDGE_ALLOWED_SENDERS=you@gmail.com`
4. **Forward** Gmail → `commander@yourdomain.com` (optional transition)
5. Email yourself (or forward) with subject:

```text
[BUILD] Portal empire tab polish
Body: Add capability snapshot to overview, mobile-friendly
```

6. Trigger sync: `POST /api/bridge/email/sync-commands` (or n8n cron every 5 min)

| Subject prefix | What happens |
|----------------|--------------|
| `[BUILD]` | High-priority task → agent queue → n8n `bridge-build` |
| `[WILL]` | Urgent will task (priority 9) |
| `[COMMAND]` | Normal task |
| `[NOTE]` | Vault inbox only |
| `[NUCLEAR]` | Decision queue — no auto-spend |

---

## Phase 0 → Command deck online → Money plays

### Phase 0 — Right now (no VPS)

| Step | Action |
|------|--------|
| 1 | GitHub mobile → new Issue → `@cursor build X` |
| 2 | cursor.com/agents → paste same order |
| 3 | Merge PRs when ready |
| 4 | `GET /api/bridge/status` after deploy — see what's live |

### Phase 1 — Command deck online

```bash
ssh your-vps
cd Command-center && git pull && docker compose up -d --build
```

- Portal: `https://your-domain.com`
- Vapi webhook: `https://your-domain.com/vapi/webhook`
- Voice tools: `https://your-domain.com/voice/tools/schema`

### Phase 2 — Start making money (KC play)

| Play | Endpoint / action |
|------|-------------------|
| Laundry host signup | `POST /api/laundry/host-signup` |
| Guest laundry request | `POST /api/laundry/guest-request` |
| Ground force mission | `POST /api/ground-force/deploy` |
| Host payment → float | `POST /api/ground-force/host-payment` |
| Expansion city lock | Voice *"Lock city node"* or API |

Revenue clears → ammo pools → sovereign acquisitions. See [SOVEREIGN_ACQUISITIONS.md](SOVEREIGN_ACQUISITIONS.md).

### Phase 3 — Upgrade the stack

Treasury manifest funds: Starlink, Peplink, sovereign mail, more VPS nodes. Empire tier rises → more ammo %, faster float clear.

---

## API

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /api/bridge/status` | Portal login | Which channels are live |
| `POST /api/bridge/command` | Portal login | Send build/will/note command |
| `POST /api/bridge/webhook` | `X-Bridge-Secret` | n8n/Zapier ingress |
| `POST /api/bridge/github` | `X-Bridge-Secret` | GitHub issue → task (via n8n) |
| `POST /api/bridge/email/sync-commands` | Portal login | IMAP sync + `[BUILD]` parsing |

## Environment

```env
# Email command bridge
BRIDGE_WEBHOOK_SECRET=generate-random-string
BRIDGE_ALLOWED_SENDERS=you@gmail.com,your.phone@carrier.com

# Sovereign mail (NOT Gmail API)
COMMS_IMAP_HOST=mail.yourdomain.com
COMMS_IMAP_USER=commander@yourdomain.com
COMMS_IMAP_PASSWORD=
COMMS_SMTP_HOST=mail.yourdomain.com
COMMS_SMTP_USER=commander@yourdomain.com
COMMS_SMTP_PASSWORD=
```

## n8n automation (optional)

| Workflow | Trigger | Action |
|----------|---------|--------|
| `bridge-email` | Cron 5 min | `POST /api/bridge/email/sync-commands` |
| `bridge-github` | GitHub new issue | `POST /api/bridge/github` with issue body |
| `bridge-build` | Webhook from Voice OS | Notify you: "High-priority build task — file @cursor issue" |

---

## Your daily loop

```text
Morning at work     → GitHub Issue @cursor (build while you earn)
Break               → Call SARA OR check portal Empire tab
Lunch               → Merge PR, comment on agent work
Evening             → Deploy VPS if new merge
Weekend             → KC laundry outreach, ground force deploy
```

You command. Agents build. Revenue funds upgrades. Gmail forwards out — you never depend on it.

See also: [GITHUB_COMMAND.md](GITHUB_COMMAND.md) · [COMMS_LAYER.md](COMMS_LAYER.md) · [FAST_LAUNCH.md](FAST_LAUNCH.md)
