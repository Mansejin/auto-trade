#!/usr/bin/env bash
# Start Bitget SCALP TrendShort ADX15 LIVE via Freqtrade (compose profile scalp).
# Prerequisite: fill exchange credentials in
#   freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json
# or mount a host secrets override. CORE Upbit bot is untouched.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Starting freqtrade-scalp-trend-short (profile scalp)..."
docker compose --profile scalp up -d bot-ft-scalp
docker compose --profile scalp ps bot-ft-scalp
echo "Logs: docker compose --profile scalp logs -f bot-ft-scalp"
