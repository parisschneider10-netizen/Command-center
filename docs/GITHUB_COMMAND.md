# GitHub Command Channel

**Primary way to talk to the hive when you're at work.** Open a GitHub Issue → Cloud Agent builds → PR lands.

Voice (SARA) is parallel. GitHub is your written command log.

## Fast loop

```text
You (work, phone, or break)
    → Open GitHub Issue on Command-center repo
    → "@cursor build X" or paste order in issue body
         ↓
Cursor Cloud Agent runs
    → Branch · code · PR
         ↓
Merge (you or hired help) → deploy VPS
```

Speed over perfection. Small fires get hired help. Nuclear stuff still goes to manifest.

## Setup (do once — 10 minutes)

### 1. Connect Cursor to GitHub

- [cursor.com](https://cursor.com) → Settings → Integrations → **GitHub**
- Install Cursor GitHub App on `parisschneider10-netizen/Command-center`
- Grant: **repo, issues, pull requests** (all read/write)

### 2. Fix Issues access (known Cursor gap)

Cloud Agents sometimes **cannot read Issues** with the default token. Fix:

1. GitHub → Settings → Developer settings → **Fine-grained PAT**
2. Scopes: `Issues: Read/Write`, `Contents: Read/Write`, `Pull requests: Read/Write`
3. Repo: `Command-center` only (or all empire repos)
4. Cursor → Cloud Agent → **Environment secrets** → add:
   ```
   GH_TOKEN=ghp_your_token_here
   ```

Without this, paste issue text directly into the agent prompt instead of referencing issue #.

### 3. How to command from GitHub

**Option A — New Issue (best for at-work)**

```markdown
Title: [BUILD] Add value node lead gen scaffold

Body:
@cursor

Fast launch. Build lead gen value node phase 1:
- n8n workflow stub
- agent endpoint in Voice OS
- log to treasury on conversion event

Ignore small lint. Ship PR. Branch: cursor/lead-gen-value-node-1894
```

**Option B — Issue comment**

Comment on any issue: `@cursor implement the above`

**Option C — cursor.com/agents**

Mobile/web → pick repo → paste same text → agent runs

**Option D — Voice (parallel)**

Call SARA → creates task in Voice OS → reference issue # in GitHub for agent

### 4. Issue labels (optional, keeps hive organized)

| Label | Meaning |
|-------|---------|
| `build` | Agent should code now |
| `will` | Commander priority — do first |
| `value-node` | Income automation |
| `deploy` | VPS / docker |
| `hire` | Needs human (RentAHuman / guardian) |
| `nuclear` | Commander decision required |

## Full GitHub org (all repos)

When you add empire repos:

1. GitHub org: `your-empire` (optional)
2. Install Cursor app on **all repos**
3. Same `GH_TOKEN` with org access
4. One issue per repo or hub repo `Command-center` routes everything

## Hired help workflow

You said you'll hire help for small fires. GitHub is how they plug in:

```text
Commander Issue (will)
    → Cloud Agent PR (code)
    → Hired human reviews merge / deploys / fixes VPS fire
    → RentAHuman for physical
```

Guardians get GitHub collaborator access (limited) or RentAHuman bounties from issues labeled `hire`.

## What NOT to put in Issues

- Passwords, API keys (use VPS `.env` only)
- Credit card numbers
- Nuclear legal decisions without `nuclear` label

## Deploy after merge

```bash
ssh your-vps
cd Command-center && git pull && docker compose up -d --build
```

Automate later with GitHub Actions — don't block launch on CI perfection.

## Speed rules (your mode)

- Merge PRs when **good enough** — iterate live
- One issue = one PR = one deploy
- Small fires → hire, don't stall the empire
- Nuclear only: money over cap, legal, public brand

GitHub is the command deck paper trail. Voice is the hotline. Agents build. Humans patch fires.
