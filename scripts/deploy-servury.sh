#!/usr/bin/env bash
# One-shot Servury deploy for Command Center (branch: cursor/sovereign-stay-matrix-1894)
# Run on the VPS as root: bash scripts/deploy-servury.sh
set -euo pipefail

DEPLOY_BRANCH="${DEPLOY_BRANCH:-cursor/sovereign-stay-matrix-1894}"
REPO_URL="${REPO_URL:-https://github.com/parisschneider10-netizen/Command-center.git}"
INSTALL_DIR="${INSTALL_DIR:-/opt/Command-center}"
PUBLIC_IP="${PUBLIC_IP:-$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')}"

echo "==> Command Center deploy (branch: $DEPLOY_BRANCH)"
echo "==> Detected public IP: $PUBLIC_IP"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git curl ca-certificates openssl

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin || true
fi

mkdir -p /opt
if [ ! -d "$INSTALL_DIR/.git" ]; then
  git clone -b "$DEPLOY_BRANCH" "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
git fetch origin "$DEPLOY_BRANCH"
git checkout "$DEPLOY_BRANCH"
git pull origin "$DEPLOY_BRANCH"

mkdir -p data vault/sovereign

if [ ! -f .env ]; then
  PORTAL_PASSWORD="$(openssl rand -base64 18)"
  cat > .env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
PORTAL_USERNAME=commander
PORTAL_PASSWORD=$PORTAL_PASSWORD
DATABASE_URL=sqlite+aiosqlite:///./data/command_center.db
CORS_ORIGINS=http://${PUBLIC_IP}:3000
PUBLIC_BASE_URL=http://${PUBLIC_IP}:8000
VAULT_PATH=./vault

N8N_WEBHOOK_BASE_URL=http://${PUBLIC_IP}:5678/webhook
N8N_HOST=${PUBLIC_IP}
N8N_PROTOCOL=http
N8N_WEBHOOK_URL=http://${PUBLIC_IP}:5678
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)

POSTGRES_USER=empire
POSTGRES_PASSWORD=$(openssl rand -hex 24)
POSTGRES_DB=empire

EXPANSION_DRY_RUN=true
TREASURY_SANDBOX_INSTANT_CLEAR=true
TREASURY_USDC_ADDRESS=
TREASURY_CRYPTO_CHAIN=base
TREASURY_CRYPTO_ASSET=USDC
SOVEREIGN_PAYMENT_MODE=auto
TZ=America/New_York
EOF
  echo "commander / $PORTAL_PASSWORD" > .portal-password
  chmod 600 .portal-password
  echo ""
  echo "Portal login: commander / $PORTAL_PASSWORD"
  echo "(Also saved to .portal-password on the VPS for GitHub Actions retrieval.)"
  echo ""
else
  echo ".env already exists; keeping existing secrets."
fi

echo "==> Building and starting containers..."
docker compose up -d --build

echo "==> Waiting for API health on localhost..."
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/health >/tmp/health.json 2>/dev/null; then
    echo
    cat /tmp/health.json
    echo
    echo "LOCAL HEALTH OK"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: API did not become healthy in 5 minutes."
    docker compose ps
    docker compose logs api --tail 80
    exit 1
  fi
  sleep 5
done

echo ""
docker compose ps
echo ""
echo "Portal:      http://${PUBLIC_IP}:3000"
echo "API health:  http://${PUBLIC_IP}:8000/health"
echo "SARA hook:   http://${PUBLIC_IP}:8000/vapi/webhook"
echo ""
echo "If public URLs fail but localhost works, open ports 3000, 8000, 5678"
echo "in the Servury firewall/security panel, then run: bash scripts/diagnose-vps.sh"
