#!/bin/sh
# Local safety copy under shared backup folder (survives accidental docker/ wipe).
# Volume is nearly full — keep only N newest archives.
set -eu
PATH=/usr/bin:/bin:$PATH
SRC=${SRC:-/volume1/docker}
DEST_ROOT=${DEST_ROOT:-/volume1/99. 백업/ohola-docker}
KEEP=${KEEP:-7}
STAMP=$(date +%Y%m%d_%H%M%S)
NAME="docker-${STAMP}.tar.gz"

mkdir -p "$DEST_ROOT"
# Stream compress; exclude regenerable junk
tar -C "$(dirname "$SRC")" \
  --exclude='docker/@eaDir' \
  --exclude='docker/**/node_modules' \
  --exclude='docker/**/.git' \
  --exclude='docker/**/__pycache__' \
  --exclude='docker/**/.venv' \
  -czf "$DEST_ROOT/$NAME" "$(basename "$SRC")"

# prune
ls -1t "$DEST_ROOT"/docker-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | while IFS= read -r old; do
  rm -f "$old"
done

ls -lh "$DEST_ROOT/$NAME"
echo "local backup ok -> $DEST_ROOT/$NAME"
