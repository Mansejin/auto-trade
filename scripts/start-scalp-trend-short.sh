#!/usr/bin/env bash
# Start Bitget SCALP TrendShort ADX15 LIVE via Freqtrade (compose profile scalp).
# Prerequisite: gitignored secrets overlay
#   freqtrade-research/user_data/config.bitget-scalp.secrets.json
# (copy from config.bitget-scalp.secrets.example.json). Do NOT put keys in the
# tracked live JSON. CORE Upbit bot is untouched.
set -euo pipefail
cd "$(dirname "$0")/.."
sec=freqtrade-research/user_data/config.bitget-scalp.secrets.json
if [[ ! -f "$sec" ]]; then
  echo "missing $sec — copy from config.bitget-scalp.secrets.example.json and fill keys" >&2
  exit 1
fi
echo "Starting freqtrade-scalp-trend-short (profile scalp)..."
docker compose --profile scalp up -d bot-ft-scalp
docker compose --profile scalp ps bot-ft-scalp
echo "Logs: docker compose --profile scalp logs -f bot-ft-scalp"
