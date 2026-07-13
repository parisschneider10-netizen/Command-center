# Ready Room — Chat Like Cursor

**You talk. You attach files. The machine executes. Sovereign.**

Same flow as this Cursor chat — but the brain lives on **your VPS**, not Anthropic/OpenAI UI.

---

## Three ways in (pick what fits)

| Channel | Best for | Upload files? |
|---------|----------|----------------|
| **Obsidian Ready Room** | Deep intent, vault-native | Drop images in `handwritten/` |
| **API chat** (`/api/ready-room/chat`) | Portal, scripts, automations | `POST /api/ready-room/chat/upload` |
| **Telegram** (optional) | Phone, voice notes, quick fire | Photos, docs, stickers → vault |

All paths → **intent** → **ledger** → **auto-execute** (when `mode: live`).

---

## Chat API (like this thread)

**Send message:**
```bash
curl -u commander:YOUR_PASSWORD -X POST \
  https://157-254-194-89.sslip.io/api/ready-room/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Launch presale for product X. Budget cap $25.","mode":"live"}'
```

**Upload file + optional caption:**
```bash
curl -u commander:YOUR_PASSWORD -X POST \
  https://157-254-194-89.sslip.io/api/ready-room/chat/upload \
  -F "file=@sketch.jpg" \
  -F "caption=Build this UI"
```

Files land in `vault/ready-room/chat/attachments/`. Images auto-run handwritten decode.

---

## Telegram setup (optional — sovereign bridge)

1. Message **@BotFather** → `/newbot` → copy token.
2. On VPS `.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_WEBHOOK_SECRET=pick-a-long-random-string
   TELEGRAM_COMMANDER_CHAT_IDS=YOUR_CHAT_ID
   ```
3. Get your chat id: message your bot, then open  
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Set webhook (once):
   ```
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://157-254-194-89.sslip.io/api/telegram/webhook&secret_token=<WEBHOOK_SECRET>"
   ```
5. Redeploy VPS workflow.

**Then:** text your bot anything. Send photos/sketches. Same Ready Room pipeline.

**Why Telegram helps (sovereign):**
- Mobile-first, file upload, notifications
- **Your** bot token on **your** VPS — not locked to big-tech chat UI
- Commander chat IDs = only you can command

**What we skip:** Telegram cloud as source of truth. Messages are **copied to vault** then processed locally.

---

## What the machine does when you chat

1. Saves transcript → `vault/ready-room/chat/`
2. Parses intent (launch, build, presale, firewall, etc.)
3. Appends **Layer 1 ledger**
4. If `mode: live` + auto_execute → runs intent pipeline
5. Replies with status (API JSON or Telegram message)

---

## Operating modes

| You say | Mode | Effect |
|---------|------|--------|
| `drill` / sights on | `drill` | Plan only, dry-run |
| `launch` / kill shot | `live` | Auto-execute |

Default in chat: **live** (max velocity). Say **drill** to rehearse.

---

## Sovereign stack

```
You (chat / voice / Telegram / Obsidian)
        ↓
   Ready Room (VPS vault)
        ↓
   Intent + ledger + caps
        ↓
   Agents / SARA / guardians / presale
```

No Replit. No Vapi dashboard for daily ops. **Keys on VPS. Vault is truth.**

---

*Chat is the bridge. Sovereignty is the destination.*
