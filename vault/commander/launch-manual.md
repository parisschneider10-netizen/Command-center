# Commander Launch Manual — Sights On, Then Kill Shot

> **You:** State intent only. Hold keys. See nuclear.  
> **Hive:** Execute, drill, spend within caps. Never overrun without your yes.

This is the full playbook. Keep `vault/commander/launch-cheat-sheet.md` on your phone.

---

## The two-phase doctrine

| Phase | Name | What happens | Your role |
|-------|------|----------------|-----------|
| **1** | **Sights on** | Dry-run, health checks, voice test, sandbox drills | Say *"drill"* or *"dry run"* |
| **2** | **Kill shot** | Live spend, live closers, live presale | Say *"launch"* or *"live"* |

**Never skip sights on** for a new play, city, or spend category. One drill costs minutes. One bad live shot costs cash and momentum.

---

## What you already have live

| Asset | URL / access |
|-------|----------------|
| **SARA voice** | +1 (971) 382-0038 |
| **Portal (HUD)** | http://157.254.194.89:3000 |
| **API health** | https://157-254-194-89.sslip.io/health |
| **Build channel** | GitHub Issue → `@cursor` |
| **Deploy** | Actions → Deploy Servury VPS |
| **Wire SARA** | Actions → Wire SARA (machine speed) |

Login: `commander` + password from deploy log (save it once).

---

## Part A — Build (one-time, mostly done)

### A1. Secrets checklist (GitHub → Settings → Secrets)

| Secret | Required |
|--------|----------|
| `VPS_HOST` | ✅ |
| `VPS_USER` | ✅ |
| `VPS_SSH_PASSWORD` | ✅ |
| `VAPI_API_KEY` | ✅ |
| `RENTAHUMAN_API_KEY` | When closers go live |
| `TREASURY_USDC_ADDRESS` | When crypto payouts live |

### A2. Deploy + wire (when code changes)

1. **Actions → Deploy Servury VPS** → branch `main`
2. **Actions → Wire SARA** → applies voice + tools
3. Confirm: `/health` shows `sara_wired: true`, doctrine `1.2`

### A3. Cheap build rule

- **Do not** hire humans for deploy, DNS, or Vapi clicks — GitHub Actions only.
- **Do not** buy domains until sslip.io HTTPS works (it does).
- **Do not** add VPS nodes until first planetary node pays for itself.

---

## Part B — Sights on (test drills)

Run these **before** every kill shot. Same commands; system stays in safe mode.

### B1. System drill (2 min)

**Voice:** Call SARA → *"Give me a briefing."*  
→ Must report real numbers from tools only (not invented).

**Portal:** Login → tasks, activity, escalations load.

**Health:** `sara_wired: true`, `velocity.empire_max_velocity: true`.

### B2. Intent drill (dry run)

**Voice or portal intent:**

> *"Sovereign stay MTR — drill only, dry run, max speed."*

Or API (portal auth): intent with `auto_execute` — system plans micro-tasks **without** live RentAHuman if keys missing.

**Pass:** Plan appears in portal. No surprise spend. Escalations route to firewall queue, not your phone.

### B3. Expansion drill

System default: `EXPANSION_DRY_RUN=true` — city locks simulate, no real VPS/GHL spend.

**Voice:**

> *"Expansion drill — one city, dry run."*

**Pass:** Activity log shows dry_run. Treasury not debited.

### B4. Presale drill (Sovereign Stay)

**Voice:**

> *"Sovereign stay simulate — KCMO sandbox."*

Uses `POST /api/sovereign-stay/simulate` path in planning — no real closer dispatched until kill shot.

### B5. Human firewall drill

**Voice:**

> *"Escalate test — firewall drill only."*

**Pass:** Escalation created. Commander **not** called. Guardian or RAH queue only.

### B6. Overwatch salvage drill

After Wire SARA: check `vault/commander/overwatch-vapi-snapshot.json` on VPS or:

> *"Migrate Overwatch — extract bones, dry run."*

---

## Part C — Kill shot (launch)

When drills pass, **one phrase** arms live execution:

### C1. Master launch command

**Call SARA or GitHub Issue:**

> *"Launch Sovereign Stay MTR. Live. Max speed. Auto execute."*

| Keyword | Effect |
|---------|--------|
| `launch` / `live` | Live mode intent |
| `max speed` / `auto execute` | Hive runs without follow-up |
| `drill` / `dry run` | Sights on only — stays safe |

### C2. What goes live (in order)

1. **Lead intake** — scrape/register MTR hosts (easiest cities first)
2. **Closer bounties** — RentAHuman $30 presale missions (needs `RENTAHUMAN_API_KEY`)
3. **Presale** — $150 at door → treasury sandbox clears → next wave
4. **Parallel nodes** — only after first $120 net float per unit

### C3. After launch — you still only intervene on nuclear

- Legal bind
- Spend above daily cap / guardian cap
- Public brand risk

Everything else: firewall + hive.

---

## Part D — Budget law (overrun prevention)

**Paramount:** Least money and energy. Cheap operations, **never** cheap quality on the system itself.

### Built-in checks (already in code)

| Guard | Default | What it blocks |
|-------|---------|----------------|
| `GUARDIAN_PER_TASK_CAP` | $25 | Auto-spend above → **nuclear queue** |
| `COMMANDER_DAILY_BUDGET_CAP` | $100/day | Treasury holds excess |
| `A2A_DAILY_CAP_USD` | $100/day | Agent hire runway |
| `EXPANSION_DRY_RUN` | `true` | No real VPS until you flip live |
| `EXPANSION_LIVE_BATCH_CAP` | 5 cities | Prevents runaway parallel spend |
| `TREASURY_SANDBOX_INSTANT_CLEAR` | `true` | Presale simulates fast — verify before live |
| Intent auto-post RAH | `true` | Only within micro-task budgets |

### Commander rules (your job)

1. **Presale funds closers** — never Commander OOP for ground force.
2. **One city proves model** → then parallel waves.
3. **Flip `EXPANSION_DRY_RUN=false` only after** first successful presale drill + kill shot in one city.
4. **Add secrets only when the play requires them** — no prepaid APIs “just in case.”
5. **Review nuclear queue weekly** — not every task.

### Energy conservation

| Do | Don't |
|----|-------|
| GitHub Issue `@cursor` for builds | SSH from phone |
| Voice one-liner intents | Repeat same order 5 times |
| Actions → Run workflow | Click Vapi/Replit dashboards |
| Portal for nuclear only | Live in portal |

---

## Part E — Weekly rhythm (minimal Commander time)

| When | Action | Time |
|------|--------|------|
| **Daily** | Optional: SARA *"Briefing."* | 30 sec |
| **Before spend** | Sights-on drill for that play | 2–5 min |
| **Launch day** | Kill-shot phrase once | 30 sec |
| **Weekly** | Portal → nuclear queue + treasury snapshot | 5 min |

---

## Part F — When something fails

| Symptom | Command |
|---------|---------|
| SARA not wired | Actions → Wire SARA |
| Deploy stale | Actions → Deploy Servury VPS |
| Fake-sounding yes from SARA | Re-run Wire SARA (verified-truth prompt) |
| Spend blocked | Portal → treasury — likely cap; nuclear approve if intentional |
| Replit/Overwatch data needed | Wire SARA + *"Extract Overwatch bones"* |

---

## Part G — Exit big tech (cheap order)

1. **Now:** Servury + GitHub Actions (done)
2. **Revenue in:** RentAHuman closers → presale float
3. **Next:** `RENTAHUMAN_API_KEY` + first live presale
4. **Then:** LiveKit voice node (treasury `voice` category) — drop Vapi rent
5. **Later:** Self-hosted agents — reduce Cursor dependency

---

## Files to know

| File | Purpose |
|------|---------|
| `vault/commander/launch-cheat-sheet.md` | One-page commands |
| `vault/commander/budget-law.md` | Overrun guards |
| `vault/commander/launch-sequence.md` | Autopilot switches |
| `manifest.json` | Sovereign OS map |
| `vault/commander/operating-contract.md` | Binding law |

---

**Remember:** Sights on → kill shot. Intent once → hive runs. Caps catch overruns. You are not the bottleneck.
