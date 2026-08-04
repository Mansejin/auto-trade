#!/bin/sh
# Install rclone static binary into ~/bin (no root).
set -eu
PATH=/usr/bin:/bin:$PATH
mkdir -p "$HOME/bin" "$HOME/tmp-rclone"
cd "$HOME/tmp-rclone"
curl -fsSL -o rclone.zip "https://downloads.rclone.org/rclone-current-linux-amd64.zip"
# Synology may lack unzip; use python
python3 - <<'PY'
import zipfile
from pathlib import Path
z = zipfile.ZipFile("rclone.zip")
z.extractall(".")
print("extracted", z.namelist()[:5])
PY
BIN=$(find "$HOME/tmp-rclone" -type f -name rclone | head -n1)
cp -f "$BIN" "$HOME/bin/rclone"
chmod 755 "$HOME/bin/rclone"
"$HOME/bin/rclone" version | head -3
rm -rf "$HOME/tmp-rclone"
echo "Installed: $HOME/bin/rclone"
echo "Next: rclone config  (create remote name exactly: gbackup)"
