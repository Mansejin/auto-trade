#!/bin/sh
set -eu
ACL=/usr/syno/bin/synoacltool
T=/volume1/docker
$ACL -get "$T"
$ACL -add "$T" "everyone::deny:rwxpdDaARWcCo:fd--" || true
$ACL -add "$T" "owner::allow:rwxpdDaARWcCo:fd--" || true
# staff denials (extra clarity; everyone deny should already cover)
for u in marketing1 marketing2 design contents jskim jslee sjoh spjeon bora swiss guest Zinus upload Zinus_agency; do
  $ACL -add "$T" "user:${u}:deny:rwxpdDaARWcCo:fd--" 2>/dev/null || true
done
chmod 750 "$T" || true
$ACL -enforce-inherit "$T" || true
echo "== final =="
$ACL -get "$T"
echo "== perms =="
for u in ohola admin marketing1 design jskim guest; do
  printf '%s -> ' "$u"
  $ACL -get-perm "$T" "$u" 2>/dev/null || echo n/a
done
ls -lad "$T"
/usr/local/bin/docker ps --format '{{.Names}} {{.Status}}' | head -20
# ohola can still list
su - ohola -s /bin/sh -c 'ls /volume1/docker | head' || ls /volume1/docker | head
echo DONE
