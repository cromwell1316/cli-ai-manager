param(
    [string]$BinDir = (Join-Path $env:LOCALAPPDATA "Programs\ai-man\bin"),
    [string]$AgyHome = (Join-Path $env:USERPROFILE "agy-homes"),
    [switch]$NoPathUpdate
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSCommandPath
$EntryPoint = Join-Path $ProjectDir "profile_manager.py"

if (-not (Test-Path -LiteralPath $EntryPoint)) {
    throw "profile_manager.py was not found next to install-windows.ps1"
}

$Python = (Get-Command py.exe -ErrorAction SilentlyContinue)
$PythonArgs = @("-3")
if (-not $Python) {
    $Python = (Get-Command python.exe -ErrorAction SilentlyContinue)
    $PythonArgs = @()
}
if (-not $Python) {
    throw "Python 3 was not found in PATH. Install Python or run from a shell where python.exe is available."
}

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
New-Item -ItemType Directory -Force -Path $AgyHome | Out-Null

$commands = @("ai-man", "profile-man", "pman")
foreach ($name in $commands) {
    $ps1 = Join-Path $BinDir "$name.ps1"
    $cmd = Join-Path $BinDir "$name.cmd"

    @"
`$env:PYTHONUTF8 = "1"
& "$($Python.Source)" $($PythonArgs -join " ") "$EntryPoint" @args
exit `$LASTEXITCODE
"@ | Set-Content -LiteralPath $ps1 -Encoding UTF8

    @"
@echo off
set PYTHONUTF8=1
"$($Python.Source)" $($PythonArgs -join " ") "$EntryPoint" %*
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath $cmd -Encoding ASCII
}

Push-Location $ProjectDir
try {
    $code = @"
from cli_profile_manager.windows_support import ensure_windows_agy_helper
ensure_windows_agy_helper(r'''$AgyHome''')
"@
    & $Python.Source @PythonArgs -c $code
    if ($LASTEXITCODE -ne 0) {
        throw "failed to install Windows agy Credential Manager helper"
    }
} finally {
    Pop-Location
}

if (-not $NoPathUpdate) {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @()
    if ($currentPath) {
        $parts = $currentPath -split ";" | Where-Object { $_ }
    }
    if ($parts -notcontains $BinDir) {
        $newPath = (($parts + $BinDir) -join ";")
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$BinDir"
    }
}

Write-Host "Installed ai-man Windows shims in $BinDir"
Write-Host "Installed agy Credential Manager helper in $AgyHome"
Write-Host "Open a new PowerShell window, then run: ai-man --help"
