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

function Test-PythonCandidate([object]$Command, [string[]]$Arguments) {
    if (-not $Command) {
        return $false
    }
    & $Command.Source @Arguments --version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Find-Python {
    $candidates = @(
        [pscustomobject]@{
            Command = (Get-Command py.exe -ErrorAction SilentlyContinue)
            Args = @("-3")
        },
        [pscustomobject]@{
            Command = (Get-Command python.exe -ErrorAction SilentlyContinue)
            Args = @()
        }
    )
    foreach ($candidate in $candidates) {
        if (Test-PythonCandidate $candidate.Command $candidate.Args) {
            return [pscustomobject]@{
                Source = $candidate.Command.Source
                Args = $candidate.Args
            }
        }
    }
    return $null
}

$Python = Find-Python
if (-not $Python) {
    throw "Python 3 was not found or could not run. Install Python 3 for Windows or open a shell where py.exe/python.exe works."
}

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
New-Item -ItemType Directory -Force -Path $AgyHome | Out-Null

$commands = @("ai-man", "profile-man", "pman")
foreach ($name in $commands) {
    $ps1 = Join-Path $BinDir "$name.ps1"
    $cmd = Join-Path $BinDir "$name.cmd"

    @"
`$env:PYTHONUTF8 = "1"
& "$($Python.Source)" $($Python.Args -join " ") "$EntryPoint" @args
exit `$LASTEXITCODE
"@ | Set-Content -LiteralPath $ps1 -Encoding UTF8

    @"
@echo off
set PYTHONUTF8=1
"$($Python.Source)" $($Python.Args -join " ") "$EntryPoint" %*
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath $cmd -Encoding ASCII
}

Push-Location $ProjectDir
try {
    $code = @"
from cli_profile_manager.windows_support import ensure_windows_agy_helper
ensure_windows_agy_helper(r'''$AgyHome''')
"@
    & $Python.Source @($Python.Args) -c $code
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
