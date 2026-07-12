# Deploy via GitHub (no phone SSH)

Use this when you have **GitHub + Servury dashboard in a browser** (work PC) but no phone SSH for 48 hours.

## Path A — GitHub Actions (recommended)

### 1. One-time secrets (5 minutes)

On GitHub: **parisschneider10-netizen/Command-center** → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Value |
|--------|--------|
| `VPS_HOST` | `157.254.194.89` |
| `VPS_USER` | `root` |
| `VPS_SSH_PASSWORD` | Root password from **Servury dashboard** (server details) |

> Optional: use `VPS_SSH_KEY` (private key) instead of password.

### 2. Deploy with one click

**Actions** → **Deploy Servury VPS** → **Run workflow** → Run

Or comment on **Issue #3**:

```markdown
@cursor deploy servury
```

### 3. Read results in GitHub

- **Actions** → latest run → **Summary** (URLs + health status)
- **Deploy via SSH** step log → portal password (`commander / …`) on first install

### 4. If deploy OK but public health fails

Servury dashboard → your server → **firewall / security** → allow inbound TCP **3000, 8000, 5678**

Re-run the workflow.

---

## Path B — Servury browser console (no GitHub secrets)

If you prefer not to store the VPS password in GitHub:

1. Log into **servury.com** dashboard (browser)
2. Open your server → **Console** (noVNC in browser — no SSH app)
3. Log in as `root` with your Servury password
4. Paste:

```bash
curl -fsSL https://raw.githubusercontent.com/parisschneider10-netizen/Command-center/cursor/sovereign-stay-matrix-1894/scripts/deploy-servury.sh | bash
```

5. Save the portal password it prints

---

## After deploy

| URL | Purpose |
|-----|---------|
| http://157.254.194.89:3000 | Portal login |
| http://157.254.194.89:8000/health | API health |
| http://157.254.194.89:8000/vapi/webhook | SARA / Vapi webhook |

**Hourly health:** Actions → **Servury health check** (runs automatically once `VPS_HOST` secret exists).

**Re-deploy after PR merges:** Run **Deploy Servury VPS** again — it `git pull`s latest branch code.
