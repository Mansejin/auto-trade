#!/usr/bin/env bash
# Deploy a strategies/{slug}.json to remote paper bot and switch STRATEGY_PATH.
# Usage:
#   ./scripts/deploy-strategy-to-bot.sh [slug]
# Defaults to current BEAR selection: krw-btc-1h-ema-adx23-obv-m5-v2
set -euo pipefail

SLUG="${1:-krw-btc-1h-ema-adx23-obv-m5-v2}"
LOCAL_FILE="$(cd "$(dirname "$0")/.." && pwd)/strategies/${SLUG}.json"
REMOTE_HOST="${REMOTE_HOST:-ubuntu@129.225.205.185}"
REMOTE_DIR="${REMOTE_DIR:-~/auto-trade}"

if [[ ! -f "$LOCAL_FILE" ]]; then
  echo "missing strategy: $LOCAL_FILE" >&2
  exit 1
fi

echo "Deploying $SLUG -> $REMOTE_HOST:$REMOTE_DIR/strategies/"
scp "$LOCAL_FILE" "$REMOTE_HOST:$REMOTE_DIR/strategies/${SLUG}.json"

ssh "$REMOTE_HOST" bash -s -- "$SLUG" "$REMOTE_DIR" <<'REMOTE'
set -euo pipefail
SLUG="$1"
DIR="${2/#\~/$HOME}"
cd "$DIR"
test -f "strategies/${SLUG}.json"
if [[ ! -f .env ]]; then
  echo "missing $DIR/.env" >&2
  exit 1
fi
# backup .env
cp .env ".env.bak.$(date +%Y%m%d_%H%M%S)"
# set STRATEGY_PATH
if grep -q '^STRATEGY_PATH=' .env; then
  sed -i "s|^STRATEGY_PATH=.*|STRATEGY_PATH=/app/strategies/${SLUG}.json|" .env
else
  echo "STRATEGY_PATH=/app/strategies/${SLUG}.json" >> .env
fi
echo "--- STRATEGY_PATH ---"
grep '^STRATEGY_PATH=' .env
docker compose up -d
docker compose ps
docker logs --tail 40 upbit-paper-bot || docker compose logs --tail 40
REMOTE

echo "Done. Active strategy: /app/strategies/${SLUG}.json"
