#!/bin/sh
# Local safety archive under /volume1/99. 백업/ohola-docker/
# Runs tar as host root via nsenter so root-owned state/risk files are included.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin:$PATH
SRC=/volume1/docker
DEST_ROOT="/volume1/99. 백업/ohola-docker"
KEEP=${KEEP:-7}
STAMP=$(date +%Y%m%d_%H%M%S)
NAME="docker-${STAMP}.tar.gz"
OUT="$DEST_ROOT/$NAME"

mkdir -p "$DEST_ROOT"

sudo -n docker run --rm --privileged --pid=host \
  -v "$DEST_ROOT:$DEST_ROOT" \
  alpine:latest nsenter -t 1 -m -u -i -n \
  sh -c "tar -C /volume1 \
    --exclude='docker/@eaDir' \
    --exclude='docker/*/node_modules' \
    --exclude='docker/*/.git' \
    --exclude='docker/*/__pycache__' \
    --exclude='docker/*/.venv' \
    -czf '$OUT' docker && chmod 640 '$OUT' && chown ohola:users '$OUT'"

# prune as ohola
ls -1t "$DEST_ROOT"/docker-*.tar.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | while IFS= read -r old; do
  rm -f "$old"
done

# quick integrity: must contain a state file path
if ! tar -tzf "$OUT" | grep -q 'p3f8c1a2/data/'; then
  echo "WARN: archive missing p3f8c1a2/data (check permissions)" >&2
fi

ls -lh "$OUT"
echo "local backup ok -> $OUT"
