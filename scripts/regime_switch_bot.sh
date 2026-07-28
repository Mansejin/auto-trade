#!/usr/bin/env bash
# Classify current KRW-BTC regime (v2) and switch remote bot STRATEGY_PATH.
# Usage:
#   bash scripts/regime_switch_bot.sh
#   DRY_RUN=1 bash scripts/regime_switch_bot.sh
#   FORCE=1 bash scripts/regime_switch_bot.sh   # ignore 24h hysteresis
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REMOTE_HOST="${REMOTE_HOST:-ubuntu@129.225.205.185}"
REMOTE_DIR="${REMOTE_DIR:-~/auto-trade}"
SSH_KEY="${SSH_KEY:-}"
DRY_RUN="${DRY_RUN:-0}"
FORCE="${FORCE:-0}"
MIN_DWELL_HOURS="${MIN_DWELL_HOURS:-24}"
LOG_FILE="${LOG_FILE:-$ROOT/reports/regime-switch-log.jsonl}"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=20)
SCP_OPTS=("${SSH_OPTS[@]}")
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
  SCP_OPTS+=(-i "$SSH_KEY")
fi

declare -A MAP=(
  [bull]="regime-bull-trend-4h-v2"
  [transition]="regime-bull-trend-4h-v2"
  [bear]="krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6"
  [sideways]="regime-sideways-mr-4h-v5"
)

echo "[regime-switch] classifying..."
python3 "$ROOT/scripts/regime_select.py" >/tmp/regime_select_out.txt
REGIME="$(python3 -c "import json;print(json.load(open('$ROOT/reports/regime-current.json'))['regime'])")"
if [[ -z "${MAP[$REGIME]+x}" ]]; then
  echo "unknown regime: $REGIME" >&2
  exit 1
fi
SLUG="${MAP[$REGIME]}"
LOCAL_JSON="$ROOT/strategies/${SLUG}.json"
test -f "$LOCAL_JSON"

OLD_SLUG="$(tr -d '[:space:]' < "$ROOT/strategies/ACTIVE_STRATEGY" 2>/dev/null || true)"
NOW_EPOCH="$(date -u +%s)"

# hysteresis: skip if same slug already active and recent switch exists
if [[ "$FORCE" != "1" && -f "$LOG_FILE" ]]; then
  LAST="$(tail -n 1 "$LOG_FILE" || true)"
  if [[ -n "$LAST" ]]; then
    LAST_TS="$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('ts_epoch',0))" "$LAST" 2>/dev/null || echo 0)"
    LAST_SLUG="$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('new_slug',''))" "$LAST" 2>/dev/null || true)"
    AGE_H=$(python3 -c "print( ($NOW_EPOCH - int('$LAST_TS'))/3600 if int('$LAST_TS')>0 else 9999 )")
    if [[ "$SLUG" == "$OLD_SLUG" && "$SLUG" == "$LAST_SLUG" ]]; then
      echo "[regime-switch] already on $SLUG for regime=$REGIME — no-op"
      exit 0
    fi
    if [[ "$SLUG" != "$OLD_SLUG" ]]; then
      # allow switch, but if last switch was very recent and flipping again, warn
      python3 -c "import sys; age=float('$AGE_H'); sys.exit(0 if age>=float('$MIN_DWELL_HOURS') else 1)" \
        || echo "[regime-switch] WARN: last switch was ${AGE_H}h ago (<${MIN_DWELL_HOURS}h). Continuing anyway because regime changed."
    fi
  fi
fi

echo "[regime-switch] regime=$REGIME -> slug=$SLUG (was=${OLD_SLUG:-none})"
echo "$SLUG" > "$ROOT/strategies/ACTIVE_STRATEGY"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[regime-switch] DRY_RUN=1 — not touching remote"
  exit 0
fi

echo "[regime-switch] syncing strategy files to $REMOTE_HOST"
scp "${SCP_OPTS[@]}" \
  "$ROOT/strategies/regime-bull-trend-4h-v2.json" \
  "$ROOT/strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json" \
  "$ROOT/strategies/regime-sideways-mr-4h-v5.json" \
  "$ROOT/strategies/ACTIVE_STRATEGY" \
  "$REMOTE_HOST:${REMOTE_DIR}/strategies/"

ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" bash -s -- "$SLUG" "$REMOTE_DIR" <<'REMOTE'
set -euo pipefail
SLUG="$1"
DIR="${2/#\~/$HOME}"
cd "$DIR"
test -f "strategies/${SLUG}.json"
cp .env ".env.bak.regime.$(date +%Y%m%d_%H%M%S)"
if grep -q '^STRATEGY_PATH=' .env; then
  sed -i "s|^STRATEGY_PATH=.*|STRATEGY_PATH=/app/strategies/${SLUG}.json|" .env
else
  echo "STRATEGY_PATH=/app/strategies/${SLUG}.json" >> .env
fi
echo "--- STRATEGY_PATH ---"
grep '^STRATEGY_PATH=' .env
docker compose up -d
docker compose restart bot
sleep 3
docker compose ps
docker logs --tail 40 upbit-paper-bot 2>&1 || docker compose logs --tail 40
REMOTE

mkdir -p "$(dirname "$LOG_FILE")"
python3 - <<PY
import json, time
from pathlib import Path
rec={
  "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "ts_epoch": int(time.time()),
  "regime": "$REGIME",
  "old_slug": """$OLD_SLUG""",
  "new_slug": "$SLUG",
  "remote": "$REMOTE_HOST",
}
Path("$LOG_FILE").parent.mkdir(parents=True, exist_ok=True)
with open("$LOG_FILE","a") as f:
  f.write(json.dumps(rec, ensure_ascii=False)+"\n")
print("[regime-switch] logged", rec)
PY

echo "[regime-switch] done"
