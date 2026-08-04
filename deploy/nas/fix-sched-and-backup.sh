#!/bin/sh
# Host-root: fix Task Scheduler paths after folder rename + ensure daily docker backup task.
set -eu
PATH=/usr/syno/bin:/usr/syno/sbin:/usr/local/bin:/usr/bin:/bin:$PATH
DB=/usr/syno/etc/esynoscheduler/esynoscheduler.db

echo "== fix scheduled task command paths =="
# Update known tasks if sqlite available
if command -v sqlite3 >/dev/null 2>&1 && [ -f "$DB" ]; then
  sqlite3 "$DB" ".tables" || true
  sqlite3 "$DB" "SELECT id,name,command FROM task;" 2>/dev/null || \
  sqlite3 "$DB" "SELECT * FROM sqlite_master;" 2>/dev/null | head -40 || true
fi

# Fallback: patch /etc/crontab does not store script body; patch via synoschedtask dump files
# Create compatibility launchers WITHOUT restoring old folder names in /volume1/docker listing:
# put wrappers under /usr/local/bin instead and point tasks there if we can edit DB.

mkdir -p /usr/local/bin/ohola-tasks
cat >/usr/local/bin/ohola-tasks/works-api-auto-pull.sh <<'E'
#!/bin/sh
exec sh /volume1/docker/p8e1b72d/api/scripts/nas-dsm-task.sh "$@"
E
cat >/usr/local/bin/ohola-tasks/ticket-queue-api-auto-pull.sh <<'E'
#!/bin/sh
exec sh /volume1/docker/p6d4a190/ticket-queue-api/scripts/nas-dsm-task.sh "$@"
E
cat >/usr/local/bin/ohola-tasks/saenggibu-auto-pull.sh <<'E'
#!/bin/sh
exec sh /volume1/docker/p2c6d9e1/scripts/nas-scheduled-pull.sh "$@"
E
cat >/usr/local/bin/ohola-tasks/saenggibu-docker-sudo.sh <<'E'
#!/bin/sh
exec sh /volume1/docker/p2c6d9e1/scripts/nas-setup-docker-sudo.sh "$@"
E
cat >/usr/local/bin/ohola-tasks/docker-backup-daily.sh <<'E'
#!/bin/sh
set -eu
/bin/sh /volume1/docker/p3f8c1a2/deploy/nas/backup-docker-local.sh
# remote optional
if [ -x /var/services/homes/ohola/bin/rclone ] && \
   /var/services/homes/ohola/bin/rclone listremotes 2>/dev/null | grep -q '^gbackup:'; then
  HOME=/var/services/homes/ohola /bin/sh /volume1/docker/p3f8c1a2/deploy/nas/backup-docker-remote.sh || true
fi
E
chmod 755 /usr/local/bin/ohola-tasks/*.sh

# Try edit task commands in DB (schema discovery)
if command -v sqlite3 >/dev/null 2>&1 && [ -f "$DB" ]; then
  for sql in \
    "UPDATE task SET command='sh /usr/local/bin/ohola-tasks/works-api-auto-pull.sh' WHERE name='works-api-auto-pull';" \
    "UPDATE task SET command='sh /usr/local/bin/ohola-tasks/ticket-queue-api-auto-pull.sh' WHERE name='ticket-queue-api-auto-pull';" \
    "UPDATE task SET command='sh /usr/local/bin/ohola-tasks/saenggibu-auto-pull.sh' WHERE name='saenggibu-auto-pull';" \
    "UPDATE task SET command='sh /usr/local/bin/ohola-tasks/saenggibu-docker-sudo.sh' WHERE name='saenggibu-docker-sudo';"
  do
    sqlite3 "$DB" "$sql" 2>/dev/null || true
  done
  synoschedtask --sync 2>/dev/null || true
fi

echo "== run local backup now =="
sh /usr/local/bin/ohola-tasks/docker-backup-daily.sh

echo "== list backup dir =="
ls -lh "/volume1/99. 백업/ohola-docker/" | head

echo "== verify archive contains data =="
NEW=$(ls -1t "/volume1/99. 백업/ohola-docker"/docker-*.tar.gz | head -1)
tar -tzf "$NEW" | grep 'p3f8c1a2/data/' | head -10 || echo 'MISSING data files'

echo "NOTE: If Task Scheduler still points at old /volume1/docker/<oldname> paths,"
echo "update in DSM UI to /usr/local/bin/ohola-tasks/*.sh"
echo "Add daily task: /usr/local/bin/ohola-tasks/docker-backup-daily.sh at 03:20"
echo DONE
