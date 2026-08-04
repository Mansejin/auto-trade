#!/usr/bin/env bash
# Classify current KRW-BTC regime (v2) and switch remote bot STRATEGY_PATH.
# Prefers server-side scripts/remote_regime_switch.py (closed-bar + guards).
# Usage:
#   bash scripts/regime_switch_bot.sh
#   DRY_RUN=1 bash scripts/regime_switch_bot.sh
#   FORCE=1 bash scripts/regime_switch_bot.sh   # bypass dwell only (not position guard)
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
TEXT_LOG="${TEXT_LOG:-$ROOT/logs/regime-switch.log}"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=20)
SCP_OPTS=("${SSH_OPTS[@]}")
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
  SCP_OPTS+=(-i "$SSH_KEY")
fi

mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$TEXT_LOG")"
log() {
  local msg="$*"
  echo "$msg"
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$msg" >>"$TEXT_LOG"
}

declare -A MAP=(
  [bull]="regime-bull-trend-4h-v2"
  [transition]="regime-bull-trend-4h-v2"
  [bear]="krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6"
  [sideways]="regime-sideways-mr-4h-v5"
)

echo "[regime-switch] classifying (closed daily bar)..."
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

if [[ "$SLUG" == "$OLD_SLUG" ]]; then
  log "[regime-switch] already on $SLUG for regime=$REGIME — no-op"
  exit 0
fi

# Hard dwell: only count action=switched rows (ignore noop/skip noise)
if [[ "$FORCE" != "1" && -f "$LOG_FILE" ]]; then
  AGE_H="$(python3 - <<PY
import json
from pathlib import Path
path = Path("$LOG_FILE")
last_ts = 0
for line in path.read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        rec = json.loads(line)
    except Exception:
        continue
    if rec.get("action") == "switched":
        last_ts = int(rec.get("ts_epoch") or 0)
print(9999 if last_ts <= 0 else ($NOW_EPOCH - last_ts) / 3600)
PY
)"
  if ! python3 -c "import sys; age=float('$AGE_H'); sys.exit(0 if age>=float('$MIN_DWELL_HOURS') else 1)"; then
    log "[regime-switch] dwell_block: last successful switch ${AGE_H}h ago (<${MIN_DWELL_HOURS}h). Keeping ${OLD_SLUG}. FORCE=1 to bypass dwell."
    python3 - <<PY
import json, time
from pathlib import Path
rec={
  "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "ts_epoch": int(time.time()),
  "regime": "$REGIME",
  "old_slug": """$OLD_SLUG""",
  "new_slug": "$SLUG",
  "action": "dwell_block",
  "dwell_age_hours": float("$AGE_H"),
  "remote": "$REMOTE_HOST",
}
Path("$LOG_FILE").parent.mkdir(parents=True, exist_ok=True)
with open("$LOG_FILE","a") as f:
  f.write(json.dumps(rec, ensure_ascii=False)+"\n")
PY
    exit 0
  fi
fi

log "[regime-switch] regime=$REGIME -> slug=$SLUG (was=${OLD_SLUG:-none})"

if [[ "$DRY_RUN" == "1" ]]; then
  log "[regime-switch] DRY_RUN=1 — not touching remote / ACTIVE_STRATEGY"
  exit 0
fi

echo "[regime-switch] syncing strategy + switcher to $REMOTE_HOST"
scp "${SCP_OPTS[@]}" \
  "$ROOT/scripts/remote_regime_switch.py" \
  "$REMOTE_HOST:${REMOTE_DIR}/scripts/"

scp "${SCP_OPTS[@]}" \
  "$ROOT/strategies/regime-bull-trend-4h-v2.json" \
  "$ROOT/strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json" \
  "$ROOT/strategies/regime-sideways-mr-4h-v5.json" \
  "$REMOTE_HOST:${REMOTE_DIR}/strategies/"

# Server path owns cancel-orders + position-skip + STRATEGY_PATH + ACTIVE_STRATEGY
log "[regime-switch] invoking remote_regime_switch.py on server (guards enabled)"
ssh "${SSH_OPTS[@]}" "$REMOTE_HOST" bash -s -- "$REMOTE_DIR" "$FORCE" <<'REMOTE'
set -euo pipefail
DIR="${1/#\~/$HOME}"
FORCE="${2:-0}"
cd "$DIR"
export FORCE
export DRY_RUN=0
python3 scripts/remote_regime_switch.py
REMOTE

# Pull authoritative ACTIVE_STRATEGY after remote may have skipped
scp "${SCP_OPTS[@]}" \
  "$REMOTE_HOST:${REMOTE_DIR}/strategies/ACTIVE_STRATEGY" \
  "$ROOT/strategies/ACTIVE_STRATEGY" 2>/dev/null || true

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
  "action": "delegated_remote_regime_switch",
  "remote": "$REMOTE_HOST",
}
Path("$LOG_FILE").parent.mkdir(parents=True, exist_ok=True)
with open("$LOG_FILE","a") as f:
  f.write(json.dumps(rec, ensure_ascii=False)+"\n")
print("[regime-switch] logged", rec)
PY

log "[regime-switch] done"
