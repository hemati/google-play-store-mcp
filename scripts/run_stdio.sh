#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=./src:${PYTHONPATH:-}
python -m googleplay_mcp.server