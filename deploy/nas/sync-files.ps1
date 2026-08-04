# NAS sync from Windows (pwsh 7). Avoids nested SSH/python quoting.
# Usage:
#   pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/static/index.html,web/static/desk.js
#   pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/static/index.html -RebuildDesk

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]] $Files,

    [string] $HostAlias = "saenggibu-nas-local",

    [string] $RemoteRoot = "/volume1/docker/p3f8c1a2",

    [switch] $RebuildDesk
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repo

$list = @()
foreach ($f in $Files) {
    foreach ($part in ($f -split ",")) {
        $p = $part.Trim()
        if (-not $p) { continue }
        if (-not (Test-Path -LiteralPath $p)) {
            throw "Missing file: $p"
        }
        $list += (Resolve-Path -LiteralPath $p).Path
    }
}
if (-not $list) { throw "No files to sync" }

$tgz = Join-Path $env:TEMP ("autotrade-nas-sync-{0}.tgz" -f [guid]::NewGuid().ToString("n"))
try {
    Push-Location $repo
    # paths relative to repo for tar members
    $rel = foreach ($abs in $list) {
        $abs.Substring($repo.Path.Length).TrimStart("\", "/") -replace "\\", "/"
    }
    & tar -czf $tgz -- $rel
    if ($LASTEXITCODE -ne 0) { throw "tar failed: $LASTEXITCODE" }
    Pop-Location

    $extractPy = @'
import base64, io, sys, tarfile
from pathlib import Path
ROOT = Path(sys.argv[1])
raw = base64.b64decode(sys.stdin.buffer.read())
with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
    members = list(tf.getmembers())
    tf.extractall(ROOT)
print("extracted", len(members), "->", ROOT)
for m in members:
    print(" ", m.name)
'@
    $extractPath = Join-Path $env:TEMP "nas_extract_once.py"
    # UTF-8 no BOM
    [IO.File]::WriteAllText($extractPath, $extractPy.Replace("`r`n", "`n"))

    Get-Content -Raw -LiteralPath $extractPath | & ssh $HostAlias "cat > /tmp/nas_extract_once.py"
    if ($LASTEXITCODE -ne 0) { throw "ssh upload extract.py failed" }

    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tgz))
    $b64 | & ssh $HostAlias "python3 /tmp/nas_extract_once.py $RemoteRoot"
    if ($LASTEXITCODE -ne 0) { throw "ssh extract failed" }

    if ($RebuildDesk) {
        $rebuild = @'
#!/bin/sh
set -e
cd /volume1/docker/p3f8c1a2
sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile tunnel up -d --build w3
sleep 3
curl -sS -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:18080/autotrade/healthz
'@
        $rebuildPath = Join-Path $env:TEMP "nas_rebuild_desk.sh"
        [IO.File]::WriteAllText($rebuildPath, ($rebuild -replace "`r`n", "`n"))
        $rb64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content -Raw $rebuildPath)))
        $writeSh = @'
import sys, base64, os
open("/tmp/nas_rebuild_desk.sh", "wb").write(base64.b64decode(sys.stdin.buffer.read()))
os.chmod("/tmp/nas_rebuild_desk.sh", 0o755)
print("wrote rebuild")
'@
        $writeShPath = Join-Path $env:TEMP "nas_write_sh.py"
        [IO.File]::WriteAllText($writeShPath, ($writeSh -replace "`r`n", "`n"))
        Get-Content -Raw $writeShPath | & ssh $HostAlias "cat > /tmp/nas_write_sh.py"
        $rb64 | & ssh $HostAlias "python3 /tmp/nas_write_sh.py && sh /tmp/nas_rebuild_desk.sh"
        if ($LASTEXITCODE -ne 0) { throw "rebuild failed" }
    }

    Write-Host "sync ok ($($list.Count) files)"
}
finally {
    Remove-Item -LiteralPath $tgz -Force -ErrorAction SilentlyContinue
}
