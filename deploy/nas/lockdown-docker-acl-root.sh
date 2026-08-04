#!/bin/sh
# Run as host root (via: docker run --privileged --pid=host ... nsenter -t 1 ... sh thisfile)
set -eu
TARGET=/volume1/docker
ACL=/usr/syno/bin/synoacltool

echo "== before =="
$ACL -get "$TARGET" | head -40

$ACL -del "$TARGET"
$ACL -set-owner "$TARGET" user root || true
$ACL -add "$TARGET" "user:ohola:allow:rwxpdDaARWcCo:fd--"
$ACL -add "$TARGET" "user:admin:allow:rwxpdDaARWcCo:fd--"
$ACL -add "$TARGET" "user:ContainerManager:allow:rwxpdDaARWc--:fd--"
$ACL -add "$TARGET" "owner::allow:rwxpdDaARWcCo:fd--"
$ACL -add "$TARGET" "everyone::deny:rwxpdDaARWcCo:fd--"
chmod 750 "$TARGET" || true
$ACL -enforce-inherit "$TARGET" || true

echo "== after =="
$ACL -get "$TARGET"
echo "== perms =="
for u in ohola admin marketing1 design jskim guest; do
  printf '%s -> ' "$u"
  $ACL -get-perm "$TARGET" "$u" 2>/dev/null || echo n/a
done
/usr/local/bin/docker ps --format '{{.Names}} {{.Status}}' | head -15 || true
echo DONE
