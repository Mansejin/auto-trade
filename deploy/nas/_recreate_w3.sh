#!/bin/sh
# Recreate desk (w3) so new strategy/condition_meters mounts apply.
set -e
cd /volume1/docker/p3f8c1a2
sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml up -d --force-recreate --no-deps w3
sleep 3
sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml ps w3
curl -sf -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:18080/healthz || true
