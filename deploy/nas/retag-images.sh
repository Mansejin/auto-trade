#!/bin/sh
set -eu
PATH=/usr/local/bin:/usr/bin:$PATH
D="sudo -n docker"

$D tag ticket-queue-api-api:latest p6d4a190-w1:latest 2>/dev/null || true
$D tag api-works-api:latest p8e1b72d-w1:latest 2>/dev/null || true
$D tag api-conti-collab:latest p8e1b72d-w2:latest 2>/dev/null || true
$D tag p2c6d9e1-sgb-api:latest p2c6d9e1-w1:latest 2>/dev/null || true
$D tag p5a0f33c-api:latest p5a0f33c-w1:latest 2>/dev/null || true

# Force container recreate with opaque image where possible
$D rm -f p6d4a190-w1 p8e1b72d-w1 p8e1b72d-w2 p5a0f33c-w1 p2c6d9e1-w1 2>/dev/null || true

TQ=/volume1/docker/p6d4a190/ticket-queue-api
if [ -f "$TQ/docker-compose.yml" ]; then
  # ensure api service uses opaque image if an image key exists
  python3 - <<'PY'
from pathlib import Path
p = Path("/volume1/docker/p6d4a190/ticket-queue-api/docker-compose.yml")
t = p.read_text(encoding="utf-8")
t2 = t
# common patterns
for a,b in [
    ("ticket-queue-api-api", "p6d4a190-w1:latest"),
]:
    t2 = t2.replace(a, b)
if t2 != t:
    p.write_text(t2, encoding="utf-8")
    print("patched ticket compose image")
else:
    print("ticket compose unchanged")
PY
  if [ -f "$TQ/docker-compose.cloudflare.yml" ]; then
    (cd "$TQ" && $D compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d)
  else
    (cd "$TQ" && $D compose -f docker-compose.yml up -d)
  fi
fi

(cd /volume1/docker/p8e1b72d/api && $D compose up -d)
(cd /volume1/docker/p5a0f33c && $D compose up -d)
(cd /volume1/docker/p2c6d9e1 && $D compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d)

# openclaw orphan rename if present
if $D ps -a --format '{{.Names}}' | grep -qx openclaw; then
  $D rename openclaw p0c9e4f5-w1 2>/dev/null || $D rm -f openclaw
fi

echo "=== names ==="
$D ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
echo "=== folders ==="
ls -1 /volume1/docker
