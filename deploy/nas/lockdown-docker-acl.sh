#!/bin/sh
# Restrict /volume1/docker to ohola (+ admin/ContainerManager/root).
# Apply as host root via nsenter (ohola cannot write Syno ACL directly):
#
#   sudo docker run --rm --privileged --pid=host \
#     -v /volume1/docker/p3f8c1a2/deploy/nas/fix-acl.sh:/tmp/fix-acl.sh:ro \
#     alpine:latest nsenter -t 1 -m -u -i -n sh /tmp/fix-acl.sh
#
set -eu
echo "Use fix-acl.sh via nsenter (see BACKUP.md)."
exit 1
