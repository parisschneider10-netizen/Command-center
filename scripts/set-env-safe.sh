#!/usr/bin/env bash
# Safely set .env keys (handles special chars in API keys).
set -euo pipefail

ENV_FILE="${1:-.env}"
shift
touch "$ENV_FILE"

set_kv() {
  local key="$1"
  local val="$2"
  [ -z "$val" ] && return 0
  grep -v "^${key}=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null || true
  mv "${ENV_FILE}.tmp" "$ENV_FILE"
  printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
}

while [ "$#" -ge 2 ]; do
  set_kv "$1" "$2"
  shift 2
done
