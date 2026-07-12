#!/usr/bin/env bash
# Run on the VPS after SSH to debug connection-reset / deploy issues.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/Command-center}"
PUBLIC_IP="${PUBLIC_IP:-$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')}"

echo "=== Command Center VPS diagnostics ==="
echo "Public IP: $PUBLIC_IP"
echo "Time: $(date -u)"
echo ""

echo "--- Docker ---"
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker compose version 2>/dev/null || true
else
  echo "Docker NOT installed. Run: bash scripts/deploy-servury.sh"
fi
echo ""

if [ -d "$INSTALL_DIR" ]; then
  cd "$INSTALL_DIR"
  echo "--- Repo ---"
  git rev-parse --abbrev-ref HEAD 2>/dev/null || true
  git log -1 --oneline 2>/dev/null || true
  echo ""

  echo "--- docker compose ps ---"
  docker compose ps 2>/dev/null || echo "(compose not runnable here)"
  echo ""

  echo "--- Local health (127.0.0.1:8000) ---"
  if curl -fsS --max-time 5 http://127.0.0.1:8000/health; then
    echo
    echo "LOCAL: OK"
  else
    echo "LOCAL: FAILED"
    echo "--- api logs (last 60 lines) ---"
    docker compose logs api --tail 60 2>/dev/null || true
  fi
  echo ""

  echo "--- Portal localhost (127.0.0.1:3000) ---"
  curl -fsS --max-time 5 -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:3000/ || echo "portal: FAILED"
  echo ""
else
  echo "Repo not found at $INSTALL_DIR"
  echo "Clone with: bash scripts/deploy-servury.sh"
  echo ""
fi

echo "--- Listening ports (8000, 3000, 5678) ---"
ss -tlnp 2>/dev/null | grep -E ':8000|:3000|:5678' || netstat -tlnp 2>/dev/null | grep -E ':8000|:3000|:5678' || echo "(ss/netstat unavailable)"
echo ""

echo "--- UFW status ---"
if command -v ufw >/dev/null 2>&1; then
  ufw status verbose || true
else
  echo "ufw not installed"
fi
echo ""

echo "--- Public curl from VPS (hairpin test) ---"
for url in "http://${PUBLIC_IP}:8000/health" "http://${PUBLIC_IP}:3000/" "http://${PUBLIC_IP}:5678/"; do
  printf "%s -> " "$url"
  curl -fsS --max-time 8 "$url" >/dev/null 2>&1 && echo OK || echo FAIL
done
echo ""

echo "=== Interpretation ==="
echo "• LOCAL OK + public FAIL  => Servury firewall: open TCP 3000, 8000, 5678 inbound"
echo "• LOCAL FAIL              => docker compose logs api; re-run deploy-servury.sh"
echo "• All ports connection reset with no docker => deploy not finished; run deploy script"
echo "• docker ps empty/unhealthy => docker compose up -d --build in $INSTALL_DIR"
