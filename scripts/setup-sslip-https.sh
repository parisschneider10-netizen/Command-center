#!/usr/bin/env bash
# Auto HTTPS for Vapi — no domain purchase. Uses sslip.io + Caddy + Let's Encrypt.
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/Command-center}"
cd "$INSTALL_DIR"

IP="${VPS_PUBLIC_IP:-$(curl -fsS https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')}"
HOST="${IP//./-}.sslip.io"
HTTPS_BASE="https://${HOST}"

echo "==> sslip.io hostname: ${HOST}"
echo "==> HTTPS base: ${HTTPS_BASE}"

cat > Caddyfile <<EOF
${HOST} {
    handle /vapi/* {
        reverse_proxy api:8000
    }
    handle /voice/* {
        reverse_proxy api:8000
    }
    handle /api/* {
        reverse_proxy api:8000
    }
    handle /auth/* {
        reverse_proxy api:8000
    }
    handle /health {
        reverse_proxy api:8000
    }
    handle /integrations/* {
        reverse_proxy api:8000
    }
    handle /vault/* {
        reverse_proxy api:8000
    }
    handle /webhook/* {
        reverse_proxy n8n:5678
    }
    handle {
        reverse_proxy portal:80
    }
}
EOF

if grep -q '^PUBLIC_HTTPS_URL=' .env 2>/dev/null; then
  sed -i "s|^PUBLIC_HTTPS_URL=.*|PUBLIC_HTTPS_URL=${HTTPS_BASE}|" .env
else
  echo "PUBLIC_HTTPS_URL=${HTTPS_BASE}" >> .env
fi

if grep -q '^VPS_PUBLIC_IP=' .env 2>/dev/null; then
  sed -i "s|^VPS_PUBLIC_IP=.*|VPS_PUBLIC_IP=${IP}|" .env
else
  echo "VPS_PUBLIC_IP=${IP}" >> .env
fi

docker compose up -d caddy
echo "==> Waiting for HTTPS (up to 90s)..."
for i in $(seq 1 18); do
  if curl -fsSk --max-time 5 "${HTTPS_BASE}/health" >/dev/null 2>&1; then
    echo "HTTPS OK: ${HTTPS_BASE}/health"
    exit 0
  fi
  sleep 5
done

echo "WARN: HTTPS not ready yet — open ports 80 and 443 in Servury firewall, then retry."
exit 0
