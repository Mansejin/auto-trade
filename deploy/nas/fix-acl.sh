#!/bin/sh
set -eu
ACL=/usr/syno/bin/synoacltool
T=/volume1/docker

echo "== archive =="
$ACL -get-archive "$T" || true
$ACL -stat "$T" || true
ls -lad "$T"

# Re-enable Syno ACL if dropped to Linux mode
$ACL -set-archive "$T" is_support_ACL || true
$ACL -set-archive "$T" has_ACL || true

# Rebuild clean ACL (no everyone allow, no administrators group)
$ACL -del "$T" || true
$ACL -set-owner "$T" user root || true
# Deny staff first
for u in marketing1 marketing2 design contents jskim jslee sjoh spjeon bora swiss guest Zinus upload Zinus_agency; do
  $ACL -add "$T" "user:${u}:deny:rwxpdDaARWcCo:fd--" || true
done
$ACL -add "$T" "user:ohola:allow:rwxpdDaARWcCo:fd--"
$ACL -add "$T" "user:admin:allow:rwxpdDaARWcCo:fd--"
$ACL -add "$T" "user:ContainerManager:allow:rwxpdDaARWc--:fd--"

echo "== final acl =="
$ACL -get "$T" || true
echo "== perms =="
for u in ohola admin marketing1 design jskim guest; do
  printf '%s -> ' "$u"
  $ACL -get-perm "$T" "$u" 2>/dev/null || echo n/a
done
ls -lad "$T"
# verify ohola listing and docker still works
ls "$T" | head
/usr/local/bin/docker ps --format '{{.Names}} {{.Status}}' | head -15
echo DONE
