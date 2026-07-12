param(
    [string]$BinDir = (Join-Path $env:LOCALAPPDATA "Programs\ai-man\bin"),
    [string]$AgyHome = (Join-Path $env:USERPROFILE "agy-homes"),
    [switch]$NoPathUpdate,
    [switch]$SkipProfileCheck
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

function Get-ProfilePaths {
    $paths = New-Object System.Collections.Generic.List[string]
    foreach ($name in @("CurrentUserCurrentHost", "CurrentUserAllHosts")) {
        try {
            $value = $PROFILE.$name
            if ($value -and -not $paths.Contains($value)) {
                $paths.Add($value)
            }
        } catch {}
    }
    if ($PROFILE -is [string] -and -not $paths.Contains($PROFILE)) {
        $paths.Add($PROFILE)
    }
    return $paths.ToArray()
}

function Test-WindowsProfileHasConflict([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $false
    }
    $text = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    return (
        $text -match "(?m)^\s*function\s+(ai-man|profile-man|pman|agy|codex)\b" -or
        $text -match "(?m)^\s*Set-Alias\s+(ai-man|profile-man|pman|agy|codex)\b" -or
        $text -match "ai-man-tui-win|agy-multiaccount\.ps1|codex-multiaccount\.ps1"
    )
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
if (-not $SkipProfileCheck) {
    $conflicts = @(Get-ProfilePaths | Where-Object { Test-WindowsProfileHasConflict $_ })
    if ($conflicts.Count -gt 0) {
        Write-Host "[WARN] PowerShell profile entries may shadow ai-man shims or reference missing legacy files:"
        foreach ($path in $conflicts) {
            Write-Host "  - $path"
        }
        Write-Host "Review without changing files: .\scripts\repair_windows_profile.ps1"
        Write-Host "Apply safe cleanup with backup: .\scripts\repair_windows_profile.ps1 -Apply -ConfirmCleanup"
    }
}
Write-Host "Open a new PowerShell window, then run: ai-man --help"
