# Compile cpp-bt with cl.exe (no cmake required)
param(
  [string]$VsPath = ""
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $PSScriptRoot

function Find-Vs {
  $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
  $p = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
  if ($p) { return $p }
  $candidate = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\2022\BuildTools"
  if (Test-Path (Join-Path $candidate "VC\Auxiliary\Build\vcvars64.bat")) { return $candidate }
  return (& $vswhere -latest -products * -property installationPath)
}

if (-not $VsPath) { $VsPath = Find-Vs }
$VcVars = Join-Path $VsPath "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path -LiteralPath $VcVars)) { throw "vcvars64.bat not found under $VsPath" }

$OutDir = Join-Path $Here "build"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Exe = Join-Path $OutDir "cpp-bt.exe"

$cmd = @"
@echo off
call "$VcVars" || exit /b 1
cd /d "$Here" || exit /b 1
cl /nologo /O2 /EHsc /std:c++17 /DNDEBUG /I include /I third_party /Fe:"$Exe" src\main.cpp src\candle.cpp /link /OUT:"$Exe"
if errorlevel 1 exit /b 1
echo built $Exe
"@
$tmp = Join-Path $env:TEMP "cpp-bt-cl.bat"
Set-Content -Path $tmp -Value $cmd -Encoding ASCII
cmd /c $tmp
if ($LASTEXITCODE -ne 0) { throw "cl build failed" }
Write-Host "ok: $Exe"
