#!/bin/sh
# Daily: copy append-only forward logs into Mansejin/auto-trade-ledger and push (commit time = tamper evidence).
# Runs as root from Synology Task Scheduler. NAS has no git -> alpine/git container. Deploy key stays on NAS.
set -eu
R=/volume1/docker/p3f8c1a2
W=$R/data/ledger-repo
KEY=/var/services/homes/ohola/.ssh/ledger_deploy
REPO=git@github.com:Mansejin/auto-trade-ledger.git
D=/usr/local/bin/docker; [ "$(id -u)" = 0 ] || D="sudo -n $D"
mkdir -p "$W"
$D run --rm --entrypoint sh \
  -v "$W":/git -v "$R/logs/forward":/forward:ro -v "$KEY":/key:ro \
  -e GIT_SSH_COMMAND="ssh -i /key -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/git/.known_hosts" \
  alpine/git -c "
set -e
git config --global --add safe.directory /git
cd /git
[ -d .git ] || git init -q -b main
git remote get-url origin >/dev/null 2>&1 || git remote add origin $REPO
git config user.name nas-ledger; git config user.email nas-ledger@users.noreply.github.com
grep -qx .known_hosts .gitignore 2>/dev/null || echo .known_hosts >> .gitignore
mkdir -p forward && cp /forward/*.jsonl forward/
git add -A
git diff --cached --quiet || git commit -q -m \"ledger \$(date -u +%Y-%m-%dT%H:%MZ)\"
git push -q origin main
git log --oneline -1
"
