# NAS sync from Windows (pwsh 7). Avoids nested SSH/python quoting.
# Fast path (default): tar/base64 sync only. Static is bind-mounted — no rebuild.
# Usage:
#   pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/static/desk.js,web/static/desk.css
#   pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/app.py -RestartDesk
#   pwsh -NoProfile -File deploy/nas/sync-files.ps1 -Files web/Dockerfile -RebuildDesk

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]] $Files,

    [string] $HostAlias = "saenggibu-nas-local",

    [string] $RemoteRoot = "/volume1/docker/p3f8c1a2",

    # Restart container only (~2-5s). Use after app.py / equity_curve.py changes.
    [switch] $RestartDesk,

    # Full image rebuild (~40s+). Only for Dockerfile / requirements / rare bake.
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

function Invoke-RemoteShell([string] $ScriptBody, [string] $RemoteName) {
    $local = Join-Path $env:TEMP $RemoteName
    [IO.File]::WriteAllText($local, ($ScriptBody -replace "`r`n", "`n"))
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((Get-Content -Raw $local)))
    $writer = @'
import sys, base64, os
path = sys.argv[1]
open(path, "wb").write(base64.b64decode(sys.stdin.buffer.read()))
os.chmod(path, 0o755)
print("wrote", path)
'@
    $wpath = Join-Path $env:TEMP "nas_write_sh.py"
    [IO.File]::WriteAllText($wpath, ($writer -replace "`r`n", "`n"))
    Get-Content -Raw $wpath | & ssh $HostAlias "cat > /tmp/nas_write_sh.py"
    $remote = "/tmp/$RemoteName"
    $b64 | & ssh $HostAlias "python3 /tmp/nas_write_sh.py $remote && sh $remote"
}

$tgz = Join-Path $env:TEMP ("autotrade-nas-sync-{0}.tgz" -f [guid]::NewGuid().ToString("n"))
$sw = [Diagnostics.Stopwatch]::StartNew()
try {
    Push-Location $repo
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
    [IO.File]::WriteAllText($extractPath, $extractPy.Replace("`r`n", "`n"))

    Get-Content -Raw -LiteralPath $extractPath | & ssh $HostAlias "cat > /tmp/nas_extract_once.py"
    if ($LASTEXITCODE -ne 0) { throw "ssh upload extract.py failed" }

    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tgz))
    $b64 | & ssh $HostAlias "python3 /tmp/nas_extract_once.py $RemoteRoot"
    if ($LASTEXITCODE -ne 0) { throw "ssh extract failed" }
    Write-Host ("sync {0:n1}s ({1} files)" -f $sw.Elapsed.TotalSeconds, $list.Count)

    if ($RebuildDesk) {
        Invoke-RemoteShell @'
#!/bin/sh
set -e
cd /volume1/docker/p3f8c1a2
sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile tunnel up -d --build w3
sleep 4
curl -sS -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:18080/autotrade/healthz || true
'@ "nas_rebuild_desk.sh"
        Write-Host ("rebuild done {0:n1}s" -f $sw.Elapsed.TotalSeconds)
    }
    elseif ($RestartDesk) {
        Invoke-RemoteShell @'
#!/bin/sh
set -e
cd /volume1/docker/p3f8c1a2
sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml restart w3
sleep 3
curl -sS -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:18080/autotrade/healthz || true
'@ "nas_restart_desk.sh"
        Write-Host ("restart done {0:n1}s" -f $sw.Elapsed.TotalSeconds)
    }
}
finally {
    Remove-Item -LiteralPath $tgz -Force -ErrorAction SilentlyContinue
}
