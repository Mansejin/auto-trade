# Upload a local script to NAS /tmp and run it (pwsh 7; no nested quoting).
# Usage:
#   pwsh -NoProfile -File deploy/nas/run-remote.ps1 -ScriptPath .\tmp_job.py
#   pwsh -NoProfile -File deploy/nas/run-remote.ps1 -ScriptPath .\job.sh -RemoteCmd 'sh /tmp/job.sh'

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ScriptPath,

    [string] $HostAlias = "saenggibu-nas-local",

    [string] $RemotePath = "",

    [string] $RemoteCmd = ""
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Missing: $ScriptPath"
}

$name = [IO.Path]::GetFileName($ScriptPath)
if (-not $RemotePath) {
    $RemotePath = "/tmp/$name"
}
if (-not $RemoteCmd) {
    if ($name -like "*.py") {
        $RemoteCmd = "python3 $RemotePath"
    } elseif ($name -like "*.sh") {
        $RemoteCmd = "sh $RemotePath"
    } else {
        throw "Pass -RemoteCmd for non-.py/.sh scripts"
    }
}

# Normalize LF for shell scripts
$bytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $ScriptPath))
if ($name -like "*.sh" -or $name -like "*.py") {
    $text = [Text.Encoding]::UTF8.GetString($bytes) -replace "`r`n", "`n" -replace "`r", "`n"
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
}

$b64 = [Convert]::ToBase64String($bytes)
$writer = @"
import sys, base64, os
path = sys.argv[1]
open(path, "wb").write(base64.b64decode(sys.stdin.buffer.read()))
if path.endswith(".sh"):
    os.chmod(path, 0o755)
print("wrote", path)
"@
$writerPath = Join-Path $env:TEMP "nas_run_remote_writer.py"
[IO.File]::WriteAllText($writerPath, ($writer -replace "`r`n", "`n"))

Get-Content -Raw -LiteralPath $writerPath | & ssh $HostAlias "cat > /tmp/nas_run_remote_writer.py"
if ($LASTEXITCODE -ne 0) { throw "upload writer failed" }

$b64 | & ssh $HostAlias "python3 /tmp/nas_run_remote_writer.py $RemotePath"
if ($LASTEXITCODE -ne 0) { throw "upload script failed" }

# RemoteCmd is passed as a single ssh argument via pwsh --% not needed: use array form
& ssh $HostAlias $RemoteCmd
exit $LASTEXITCODE
