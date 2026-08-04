# NAS `/volume1/docker` backup + ACL

## 1) Exchange IP

NAS egress: `115.142.61.173`

```bash
# Bitget should succeed after allowlist
sudo docker exec -w /app p3f8c1a2-w2 python -c "..."
```

If Upbit still returns `invalid_access_key`, re-issue the Upbit Open API key (IP allowlist alone may not fix a revoked/wrong key).

## 2) Backups

Docker tree is ~155MB. Two layers:

### A) Local (on now)

Copies into `/volume1/99. 백업/ohola-docker/` (keeps 7 archives). Survives someone deleting `/volume1/docker`.

```bash
sh /volume1/docker/p3f8c1a2/deploy/nas/backup-docker-local.sh
```

### B) Remote Google Drive / GCS (rclone)

```bash
sh /volume1/docker/p3f8c1a2/deploy/nas/install-rclone.sh   # already done once
~/bin/rclone config
# remote name MUST be: gbackup
```

Prefer **GCS service account JSON** under `~/secrets/` (outside docker share).

```bash
sh /volume1/docker/p3f8c1a2/deploy/nas/backup-docker-remote.sh
# REMOTE=gbackup:bucket-or-folder  KEEP_REMOTE=14
```

### Cron (ohola)

```bash
sh /volume1/docker/p3f8c1a2/deploy/nas/install-backup-cron.sh
# 03:20 local, 03:35 remote (remote no-ops until gbackup exists)
```

## 3) ACL lockdown (ohola-only)

Applied. Staff → deny; `ohola` / `admin` / `ContainerManager` / root owner → allow.

Re-apply:

```bash
sudo docker run --rm --privileged --pid=host \
  -v /volume1/docker/p3f8c1a2/deploy/nas/fix-acl.sh:/tmp/fix-acl.sh:ro \
  alpine:latest nsenter -t 1 -m -u -i -n sh /tmp/fix-acl.sh
```

Does not change `sudo docker` runtime. Optional DSM: hide shared folder from users without permission.
