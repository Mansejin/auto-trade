#!/bin/sh
# Install ohola crontab: local daily + remote if gbackup configured.
set -eu
HOME=${HOME:-/var/services/homes/ohola}
DEPLOY=/volume1/docker/p3f8c1a2/deploy/nas
LOGDIR=$HOME/docker-backup-logs
mkdir -p "$LOGDIR"

TMP=$(mktemp)
crontab -l 2>/dev/null | grep -v 'backup-docker-' >"$TMP" || true
echo "20 3 * * * /bin/sh $DEPLOY/backup-docker-local.sh >>$LOGDIR/local.log 2>&1" >>"$TMP"
echo "35 3 * * * /bin/sh $DEPLOY/backup-docker-remote.sh >>$LOGDIR/remote.log 2>&1" >>"$TMP"
crontab "$TMP"
rm -f "$TMP"
crontab -l
echo "cron installed"
