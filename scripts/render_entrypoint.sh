#!/usr/bin/env bash
# Decode service account from an environment variable and run the MCP server.
set -euo pipefail

if [[ -n "${SERVICE_ACCOUNT_JSON_B64:-}" ]]; then
  mkdir -p /app/secrets
  printf '%s' "$SERVICE_ACCOUNT_JSON_B64" | base64 -d > /app/secrets/service_account.json
  export GOOGLE_SERVICE_ACCOUNT_JSON=/app/secrets/service_account.json
fi

exec "$@"
