# Comms Layer — Gmail Replacement

Replace Gmail with **sovereign mail + agent inbox**. You never open an inbox again — agents do.

## Target architecture

```text
                    yourdomain.com
                         │
              ┌──────────┴──────────┐
              │  Stalwart Mail      │  Self-hosted on VPS (sovereign)
              │  or Mailcow         │  OR Migadu/Fastmail (Phase 1 bridge)
              └──────────┬──────────┘
                         │ IMAP / SMTP
              ┌──────────┴──────────┐
              │  Voice OS Comms API │  /api/comms/*
              │  unified inbox      │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    Triage agent    Reply agent     Archive to vault
    (AutoGen)       (draft/send)    (Obsidian)
```

## Why not Gmail

| Gmail | Empire comms |
|-------|----------------|
| Google owns your data | You own mail on your VPS |
| Manual inbox | Agents triage 24/7 |
| No API for agents | First-class agent inbox API |
| Surveillance/ad model | Sovereign |

## Phased rollout

### Phase 1 — Bridge (go live fast)

Use a custom domain on **Migadu** or **Fastmail** (~$19/yr):
- Point MX to provider
- Voice OS connects via IMAP/SMTP credentials in `.env`
- Agents read/send through comms API
- You stop opening Gmail — agents handle it

### Phase 2 — Sovereign (when ready)

Self-host **Stalwart** on same VPS:

```yaml
# docker-compose.yml (uncomment when ready)
stalwart:
  image: stalwartlabs/stalwart:latest
  ports:
    - "25:25"
    - "587:587"
    - "993:993"
  volumes:
    - stalwart_data:/opt/stalwart
```

Full ownership. Same comms API — swap credentials only.

## Agent email workflow

1. **Inbound** — cron or n8n polls IMAP → `POST /api/comms/sync`
2. **Triage agent** — classify: reply/auto/archive/escalate
3. **Draft agent** — writes reply, stores in comms DB
4. **Send rules** (from will manifest):
   - Routine → agent sends via SMTP
   - Nuclear → queue in Commander portal for yes/no
5. **Archive** — copy thread summary to `vault/comms/`

## Voice commands (SARA)

- *"Any email needing me?"* → agents summarize, nuclear only if flagged
- *"Draft reply to latest vendor email"* → agent queue task
- *"Send the draft"* → if under manifest auto-send rules

## Environment variables

```env
COMMS_IMAP_HOST=mail.yourdomain.com
COMMS_IMAP_PORT=993
COMMS_IMAP_USER=commander@yourdomain.com
COMMS_IMAP_PASSWORD=
COMMS_SMTP_HOST=mail.yourdomain.com
COMMS_SMTP_PORT=587
COMMS_SMTP_USER=commander@yourdomain.com
COMMS_SMTP_PASSWORD=
COMMS_FROM_NAME=Commander
COMMS_AUTO_SEND_ROUTINE=true
```

## API endpoints (Voice OS)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/comms/sync` | Pull new mail from IMAP |
| `GET /api/comms/inbox` | Agent-readable inbox |
| `GET /api/comms/messages/{id}` | Full message |
| `POST /api/comms/draft` | Agent creates draft reply |
| `POST /api/comms/send/{id}` | Send (checks manifest rules) |

## Dev/testing

Use **Mailpit** locally (optional docker profile) — catches all outbound mail, no real SMTP needed while building agents.

## Migration from Gmail

1. Set up domain mail (Phase 1 provider or Stalwart)
2. Add forward from Gmail → new address (transition period)
3. Point agents at comms API
4. Stop checking Gmail when agents handle 95%+
5. Close Gmail or keep as archive-only

Your empire doesn't run on Google's inbox. It runs on agents reading **your** mail server.
