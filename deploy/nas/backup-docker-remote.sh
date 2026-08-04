#!/bin/sh
# Stream /volume1/docker to remote (rclone). No large local copy (volume is near full).
# Requires: ~/.config/rclone/rclone.conf with remote named "gbackup"
# Example remotes: Google Drive or GCS.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin:$HOME/bin:$PATH

SRC=${SRC:-/volume1/docker}
REMOTE=${REMOTE:-gbackup:ohola-nas-docker}
STAMP=$(date +%Y%m%d_%H%M%S)
NAME="docker-${STAMP}.tar.gz"
LOG_DIR=${LOG_DIR:-$HOME/docker-backup-logs}
KEEP_REMOTE=${KEEP_REMOTE:-14}
RCLONE_BIN=${RCLONE_BIN:-rclone}

mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/backup-${STAMP}.log"

if ! command -v "$RCLONE_BIN" >/dev/null 2>&1; then
  echo "rclone not found. Install to ~/bin/rclone first." | tee -a "$LOG"
  exit 1
fi

if ! "$RCLONE_BIN" listremotes | grep -q '^gbackup:'; then
  echo "rclone remote 'gbackup:' missing. Configure first." | tee -a "$LOG"
  exit 1
fi

echo "[$(date -Iseconds)] start $SRC -> ${REMOTE}/${NAME}" | tee -a "$LOG"

# Exclude noisy/regenerable paths; still include .env and compose (critical).
tar -C "$(dirname "$SRC")" \
  --exclude='docker/@eaDir' \
  --exclude='docker/**/node_modules' \
  --exclude='docker/**/.git' \
  --exclude='docker/**/__pycache__' \
  --exclude='docker/**/.venv' \
  --exclude='docker/**/logs/*.log' \
  -czf - "$(basename "$SRC")" \
  | "$RCLONE_BIN" rcat --s3-no-check-bucket --retries 5 "${REMOTE}/${NAME}" \
  2>>"$LOG"

echo "[$(date -Iseconds)] uploaded ${REMOTE}/${NAME}" | tee -a "$LOG"

# Prune old remote archives (keep newest KEEP_REMOTE)
"$RCLONE_BIN" lsf "${REMOTE}" --files-only \
  | grep '^docker-[0-9T_]*\.tar\.gz$' \
  | sort -r \
  | tail -n +"$((KEEP_REMOTE + 1))" \
  | while IFS= read -r old; do
      echo "delete old $old" | tee -a "$LOG"
      "$RCLONE_BIN" deletefile "${REMOTE}/${old}" || true
    done

echo "[$(date -Iseconds)] done" | tee -a "$LOG"
