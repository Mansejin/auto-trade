#!/bin/sh
# Daily Policy C regime switch for NAS opaque compose.
# Synology Task Scheduler: run as root, daily 00:20 KST (after 1d bar close).
set -e
export AUTO_TRADE_ROOT=/volume1/docker/p3f8c1a2
export COMPOSE_PROJECT_NAME=p3f8c1a2
export COMPOSE_FILE=docker-compose.nas.yml
export BOT_COMPOSE_SERVICE=w1
export BOT_CONTAINER=p3f8c1a2-w1
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
# docker CLI for the switcher (no sudo here if task runs as root)
cd "$AUTO_TRADE_ROOT"
python3 "$AUTO_TRADE_ROOT/scripts/remote_regime_switch.py" >>"$AUTO_TRADE_ROOT/logs/regime-switch.cron.log" 2>&1
