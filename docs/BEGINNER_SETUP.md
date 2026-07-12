# Beginner Setup — No Tech Background Required

You asked: *"Do I click something on Servury to connect GitHub?"*

**No.** Servury and GitHub are two different things. Nothing auto-connects. You link them with a few simple steps below — or hire someone for Step 3.

---

## The three pieces (simple mental model)

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GITHUB    │     │   CURSOR    │     │  SERVURY    │
│  your code  │────►│  me (agent) │     │  your VPS   │
│  storage    │     │  builds PRs │     │  runs 24/7  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                        ▲
       │         you copy code to VPS           │
       └────────────────────────────────────────┘
              (git clone / git pull)
```

| Thing | What it is | You use it to… |
|-------|------------|----------------|
| **GitHub** | Website that stores your project code | Command me via Issues, merge updates |
| **Cursor** | App where the AI agent builds code | Connect once to GitHub — I read/write the repo |
| **Servury** | A computer you rent on the internet (VPS) | Run Command Center 24/7 so SARA + portal work |

**Servury does NOT need a "Connect GitHub" button.** You copy the code from GitHub onto Servury once, then run it.

---

## Part 1 — Connect Cursor to GitHub (5 minutes, do at home)

This lets **me** build when you file GitHub Issues. Servury is not involved.

1. Go to [cursor.com](https://cursor.com) and log in
2. Click **Settings** (gear icon)
3. Click **Integrations** → **GitHub**
4. Click **Connect** and approve access to your `Command-center` repo
5. Done — when you write `@cursor` in a GitHub Issue, I can build

**Optional but helpful:** GitHub → Settings → Developer settings → Fine-grained token → give Cursor `Issues` + `Contents` access. Add as `GH_TOKEN` in Cursor Cloud Agent secrets. See [GITHUB_COMMAND.md](GITHUB_COMMAND.md).

You never give me your GitHub password in chat.

---

## Part 2 — Command me from your phone (works BEFORE Servury)

You can build **right now** without Servury:

1. Install **GitHub** app on your phone
2. Open repo: `parisschneider10-netizen/Command-center`
3. Tap **Issues** → **New issue**
4. Paste:

```markdown
Title: [BUILD] First deploy help

@cursor

I'm new to tech. Create a simple deploy checklist and verify PR #1 is ready to merge.
```

5. Submit — Cloud Agent works on a branch and opens a PR

**This is your command channel at work.** No Servury needed yet.

---

## Part 3 — Put the code ON Servury (the "connection")

This is what people mean by "deploy." You are **downloading your GitHub project onto your Servury server** and starting it.

### What you need from Servury

Log into Servury dashboard and find:

| Info | Example | Where |
|------|---------|-------|
| **Server IP** | `123.45.67.89` | Server details page |
| **Root password** OR **SSH key** | (you set this when you created the VPS) | Email or Servury panel |

You do **not** need a GitHub button in Servury.

### Option A — Hire someone (easiest if you're new)

Post on RentAHuman or Fiverr:

> "SSH into my Ubuntu VPS at IP ___. Clone https://github.com/parisschneider10-netizen/Command-center, copy .env.example to .env, run `docker compose up -d --build`. Send me the portal URL when health check works."

Cost: often $25–75 one-time.

When they finish, you get:
- Portal: `http://YOUR_IP:3000`
- Login: `commander` / password you chose in `.env`

### Option B — Do it yourself (copy-paste)

**You need:** A Mac or Windows computer at home (not your work laptop if locked down).

#### B1. Open Terminal (Mac) or PowerShell (Windows)

Mac: Spotlight → type `Terminal` → Enter

#### B2. SSH into Servury

Replace `YOUR_IP` with your real Servury IP:

```bash
ssh root@YOUR_IP
```

- First time it asks "Are you sure?" → type `yes` → Enter
- Enter your Servury root password when prompted

You are now **inside** your server. Text on screen is normal.

#### B3. Install Docker (one-time)

Paste this whole block and press Enter:

```bash
curl -fsSL https://get.docker.com | sh
```

Wait until it finishes (1–3 minutes).

#### B4. Download your project from GitHub

```bash
git clone https://github.com/parisschneider10-netizen/Command-center.git
cd Command-center
```

This **is** the GitHub → Servury connection. `git clone` copies the repo.

#### B5. Create your secret settings file

```bash
cp .env.example .env
nano .env
```

Change these lines (use arrow keys, type, save):

```env
SECRET_KEY=paste-a-long-random-sentence-here
PORTAL_PASSWORD=PickAStrongPassword123
PUBLIC_BASE_URL=http://YOUR_IP:8000
```

Save in nano: `Ctrl+O` → Enter → `Ctrl+X`

**Never paste API keys in GitHub Issues or chat.** Only on the server in `.env`.

#### B6. Start everything

```bash
docker compose up -d --build
```

First run takes 5–15 minutes. Wait.

#### B7. Check it worked

```bash
curl http://localhost:8000/health
```

You should see `"status":"ok"`.

#### B8. Open the portal

On your phone browser: `http://YOUR_IP:3000`

Login: `commander` / the password you set in `.env`

**You now have a command deck.**

---

## Part 4 — After deploy: connect SARA (voice)

1. Go to [dashboard.vapi.ai](https://dashboard.vapi.ai)
2. Open your assistant
3. Set **Server URL** to: `http://YOUR_IP:8000/vapi/webhook`  
   (Use `https://yourdomain.com` once you add a domain + HTTPS)
4. Call your Vapi number
5. Say: *"Give me a briefing"*

---

## Part 5 — Keeping GitHub and Servury in sync later

When I merge new code to GitHub, update your server:

```bash
ssh root@YOUR_IP
cd Command-center
git pull
docker compose up -d --build
```

Do this after each merge, or hire someone on a schedule.

**Still no Servury-GitHub button** — just `git pull`.

---

## What connects to what (cheat sheet)

| Connection | How | Where |
|------------|-----|-------|
| Cursor ↔ GitHub | Cursor Settings → Integrations | cursor.com |
| You ↔ me (build orders) | GitHub Issue `@cursor` | GitHub app on phone |
| GitHub ↔ Servury | `git clone` then `git pull` | SSH terminal on VPS |
| SARA ↔ Servury | Vapi webhook URL | dashboard.vapi.ai |
| API keys (GHL, Servury, etc.) | `.env` file on VPS only | Never in chat |

---

## If you get stuck

GitHub Issue:

```markdown
@cursor [BLOCKED] Deploy help

I'm on step ___. Error message: (paste here, NO passwords)
```

Or call SARA once voice is wired.

---

## Your order of operations (today)

```text
□ 1. Cursor → connect GitHub          (5 min, home)
□ 2. GitHub Issue → @cursor            (2 min, phone — works now)
□ 3. Servury → git clone + docker      (hire help OR 30 min at home)
□ 4. Vapi webhook → your server IP     (10 min)
□ 5. Call SARA → "briefing"            (test)
□ 6. Start KC laundry play             (money)
```

You are not behind. Most founders hire step 3 the first time. That's smart, not cheating.

See also: [COMMUNICATION_BRIDGE.md](COMMUNICATION_BRIDGE.md) · [DO_NOW.md](DO_NOW.md) · [GITHUB_COMMAND.md](GITHUB_COMMAND.md)
