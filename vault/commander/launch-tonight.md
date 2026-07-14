# Launch Tonight — Commander

> **One portal. One call. Feed leads. Presale. Go.**

---

## Your two controls

| Control | How |
|---------|-----|
| **Portal** | `http://157.254.194.89:3000` → **Launch** tab |
| **Voice** | **+1 (971) 382-0038** — SARA |

Everything else is optional transport (Telegram, GHL webhook, Obsidian).

---

## Tonight sequence (45 min)

### 1. Deploy (GitHub Actions — no SSH)

1. **Deploy Servury VPS**
2. **Wire SARA**

### 2. Health check

`https://157-254-194-89.sslip.io/health` → `sara_wired: true`

### 3. Feed leads (pick one)

**Portal (easiest):** Launch tab → Add Lead

**Public webhook (GHL / scrape tool):**
```
POST https://157-254-194-89.sslip.io/api/leads/intake
Content-Type: application/json

{
  "name": "Jane Host",
  "phone": "5551234567",
  "city": "Kansas City",
  "email": "jane@example.com"
}
```

**Telegram (optional):** text your bot:
```
lead: Jane Host, 5551234567, Kansas City
```

**Voice:** call SARA → *"Register lead Jane Host Kansas City 555-123-4567"*

### 4. Drill (sights on)

Portal Launch tab → **Run drill**  
Or call SARA: *"Sovereign stay drill — dry run"*

### 5. Kill shot (live)

Call SARA:
> *"Launch Sovereign Stay MTR. Live. Max speed. Auto execute."*

Or portal Launch tab → flip **Live presale** → record when closer collects $150.

---

## Presale at the door

When closer has $150 + proof:

**Portal:** Launch tab → Record presale

**API:**
```json
POST /api/sovereign-stay/presale
{
  "host_name": "Jane Host",
  "property_address": "123 Main St",
  "city_grid": "Kansas City",
  "worker_ref": "rah:closer-id",
  "proof_notes": "Cash App screenshot",
  "dry_run_closer": false
}
```

With `EMPIRE_LAUNCH_MODE=true`, closers default **live** (set `dry_run_closer: true` only to rehearse).

---

## Secrets you need for live closers

| Secret | Why |
|--------|-----|
| `RENTAHUMAN_API_KEY` | $30 closer bounties at door |
| `LEAD_WEBHOOK_SECRET` | (optional) lock public lead webhook |

Presale pays closers — Commander $0 OOP.

---

## Budget guards

| Cap | Limit |
|-----|-------|
| Per human task | $25 |
| Commander daily | $100 |
| Expansion | DRY RUN until first presale succeeds |

---

## After first presale

1. Treasury instant-clear → ammo for next wave
2. Flip `EXPANSION_DRY_RUN=false` for city locks (one city first)
3. Compound — parallel cities when funded

---

*Portal + call. Leads in. Presale out. Sovereign.*
