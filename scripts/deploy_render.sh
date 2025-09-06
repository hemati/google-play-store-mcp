#!/usr/bin/env bash
# Deploy the MCP server to Render in the EU region with basic authentication.

set -euo pipefail

if ! command -v render >/dev/null 2>&1; then
  echo "render CLI not found. Install from https://render.com/docs/cli" >&2
  exit 1
fi

: "${RENDER_API_KEY:?Set RENDER_API_KEY to your Render API key}"
: "${BASIC_AUTH_USER:?Set BASIC_AUTH_USER for HTTP basic auth}"
: "${BASIC_AUTH_PASSWORD:?Set BASIC_AUTH_PASSWORD for HTTP basic auth}"
SERVICE_ACCOUNT_JSON_PATH=${SERVICE_ACCOUNT_JSON_PATH:-secrets/service_account.json}
if [[ ! -f "$SERVICE_ACCOUNT_JSON_PATH" ]]; then
  echo "Service account JSON not found at $SERVICE_ACCOUNT_JSON_PATH" >&2
  exit 1
fi

# Authenticate the CLI
render login --api-key "$RENDER_API_KEY"

# Export credentials used by render.yaml
SERVICE_ACCOUNT_JSON_B64=$(base64 "$SERVICE_ACCOUNT_JSON_PATH" | tr -d '\n')
export BASIC_AUTH_USER BASIC_AUTH_PASSWORD SERVICE_ACCOUNT_JSON_B64

# Deploy blueprint to EU region (Frankfurt)
render blueprint deploy render.yaml
