#!/bin/sh
set -eu
grep -R "works-api-auto-pull" /usr/syno/etc /usr/local/etc 2>/dev/null | head -20
echo ----
grep -R "works-site" /usr/syno/etc /usr/local/etc 2>/dev/null | head -20
echo ----
ls -la /usr/syno/etc/synoschedule.d /usr/local/etc/synoschedule.d 2>/dev/null
find /usr/syno/etc /usr/local/etc -name '*.sqlite' -o -name '*sched*.db' 2>/dev/null | head -30
