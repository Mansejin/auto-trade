#!/bin/bash
set -euo pipefail

LOG_DIR="/home/ubuntu/auto-trade/logs"
LOG_FILE="$LOG_DIR/mem-guard.log"
THRESHOLD_PCT="${MEM_GUARD_THRESHOLD:-80}"
MIN_AVAILABLE_MB="${MEM_GUARD_MIN_AVAILABLE_MB:-120}"
COOLDOWN_SEC="${MEM_GUARD_COOLDOWN_SEC:-1800}"  # 30 min between cleans
STAMP_FILE="/tmp/mem-guard.last"

mkdir -p "$LOG_DIR"
ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "$(ts) $*" >> "$LOG_FILE"; }

read_mem() {
  local total_kb avail_kb
  total_kb=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
  avail_kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
  echo "$total_kb $avail_kb"
}

read -r TOTAL_KB AVAIL_KB < <(read_mem)
USED_KB=$((TOTAL_KB - AVAIL_KB))
USED_PCT=$((USED_KB * 100 / TOTAL_KB))
AVAIL_MB=$((AVAIL_KB / 1024))
USED_MB=$((USED_KB / 1024))
TOTAL_MB=$((TOTAL_KB / 1024))

NEED_CLEAN=0
if [ "$USED_PCT" -ge "$THRESHOLD_PCT" ]; then
  NEED_CLEAN=1
fi
if [ "$AVAIL_MB" -le "$MIN_AVAILABLE_MB" ]; then
  NEED_CLEAN=1
fi

if [ "$NEED_CLEAN" -eq 0 ]; then
  exit 0
fi

NOW=$(date +%s)
if [ -f "$STAMP_FILE" ]; then
  LAST=$(cat "$STAMP_FILE" 2>/dev/null || echo 0)
  if [ $((NOW - LAST)) -lt "$COOLDOWN_SEC" ]; then
    log "SKIP cooldown | used=${USED_PCT}% avail=${AVAIL_MB}MB"
    exit 0
  fi
fi

log "CLEAN start | used=${USED_MB}MB/${TOTAL_MB}MB (${USED_PCT}%) avail=${AVAIL_MB}MB"
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
echo "$NOW" > "$STAMP_FILE"

read -r TOTAL_KB2 AVAIL_KB2 < <(read_mem)
USED_KB2=$((TOTAL_KB2 - AVAIL_KB2))
USED_PCT2=$((USED_KB2 * 100 / TOTAL_KB2))
AVAIL_MB2=$((AVAIL_KB2 / 1024))
log "CLEAN done  | used=$((USED_KB2 / 1024))MB/${TOTAL_MB}MB (${USED_PCT2}%) avail=${AVAIL_MB2}MB"
