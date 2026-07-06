# Building From Work — GitHub + Voice + Cursor

How you build the empire foundation while on the clock — without needing your phone or laptop open.

## The loop (what actually works)

```text
AT WORK                         LATER / 24-7
────────                        ────────────
You call SARA (Vapi)            Cursor Cloud Agent runs on GitHub
    ↓                               ↓
Voice OS creates tasks          Reads tasks, vault, will manifest
Dumps notes to vault            Builds on branch, opens PR
Issues will / priorities        You review in portal + GitHub
    ↓                               ↓
Command Center logs it          Merge when ready — no impulse required
```

You **command** at work. The **hive builds** when you have connectivity to the system (Cloud Agent, n8n, future workers).

## GitHub access — what I need (and don't need)

I don't need your GitHub password. I need **repos connected to Cursor** with Cloud Agents enabled.

### One-time setup (do this once at home)

1. **GitHub → Cursor**
   - Cursor Settings → GitHub → connect account
   - Authorize access to `Command-center` repo (and any empire repos you add)

2. **Cloud Agents**
   - Ensure Cloud Agents are enabled for your Cursor account
   - This repo (`parisschneider10-netizen/Command-center`) is already the foundation

3. **Add repos when needed**
   - New empire projects = new GitHub repos
   - Connect each to Cursor so agents can work across the full empire

4. **VPS deploy** (separate from GitHub)
   - GitHub = code + PRs
   - Servury VPS = running Voice OS, n8n, portal 24/7
   - Push to `main` → deploy via `docker compose` on VPS (or CI later)

### What I can do with GitHub access

| Yes | No |
|-----|-----|
| Read/write code in connected repos | Access repos you didn't connect |
| Create branches, commit, push, open PRs | Access private repos outside Cursor |
| Work from your voice-queued tasks | Log into GitHub.com as you |
| Build foundation meticulously on PRs | Merge without your review (you control merge) |

### Your at-work commands (SARA)

| Say this | What happens |
|----------|--------------|
| *"Issue will: add treasury dashboard to portal, priority 9"* | High-priority task → agent queue |
| *"Dump to vault: value node should be X not Y"* | Note in Obsidian inbox for next build session |
| *"Create task: scaffold value extraction node phase 1"* | Task logged + n8n webhook |
| *"Nuclear: approve spend on domain mail"* | Portal queue only — not impulse spend |

**Impulse control:** Voice creates **tasks and notes**, not instant merges or payments. You review in the portal when you have internet.

## Recommended GitHub workflow

```text
main (stable, deployed to VPS)
  └── cursor/feature-name-1894 (Cloud Agent PRs)
         └── you review → merge when calm, not rushed
```

Rules for meticulous builds:
- **No direct pushes to `main` from voice** — always PR
- **One feature per PR** — small, reviewable
- **Will manifest** defines priority — agents don't chase shiny objects
- **Nuclear queue** for money, legal, public — never voice-instant

## If you want "full GitHub" across all repos

1. Create a GitHub **organization** for the empire (optional, clean)
2. Add all empire repos under it
3. Connect org to Cursor with repo access
4. Tell SARA which repo a task targets (or default: `Command-center`)

## Connecting voice tasks → Cloud Agent builds

**Now:** You call → task in DB → you (or Cloud Agent session) pick up task manually

**Next (n8n workflow):**
```text
agent-queue webhook
  → check will_priority >= 7
  → trigger Cursor Cloud Agent (when API available)
  OR notify you: "High will task ready for agent session"
```

**Future:** Standing Cloud Agent cron — polls open tasks, builds on branch, opens draft PR.

## Checklist before your next work shift

- [ ] Vapi connected to Voice OS on VPS
- [ ] GitHub connected to Cursor
- [ ] This repo pushed and PR workflow understood
- [ ] `vault/commander/will-manifest.md` has this week's priorities
- [ ] You know: call SARA = command, not panic-build

You message the system. The system builds. You merge when ready.
