param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA "Programs\ai-man"),
    [string]$BinDir,
    [string]$AppDir,
    [string]$AgyHome = (Join-Path $env:USERPROFILE "agy-homes"),
    [switch]$NoPathUpdate,
    [switch]$SkipProfileCheck,
    [switch]$DevSource,
    [switch]$Rollback,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSCommandPath
if (-not $BinDir) {
    $BinDir = Join-Path $InstallRoot "bin"
}
if (-not $AppDir) {
    $AppDir = Join-Path $InstallRoot "app"
}
$SourceEntryPoint = Join-Path $ProjectDir "profile_manager.py"

function Get-InstallBackupDir {
    return Join-Path $InstallRoot ("app.rollback-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
}

function Get-LatestInstallBackup {
    if (-not (Test-Path -LiteralPath $InstallRoot -PathType Container)) {
        return $null
    }
    $backup = Get-ChildItem -LiteralPath $InstallRoot -Directory -Filter "app.rollback-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($backup) {
        return $backup.FullName
    }
    return $null
}

function Remove-InstalledCommands {
    foreach ($name in @("ai-man", "profile-man", "pman")) {
        Remove-Item -LiteralPath (Join-Path $BinDir "$name.ps1") -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath (Join-Path $BinDir "$name.cmd") -Force -ErrorAction SilentlyContinue
    }
}

if ($Uninstall) {
    Remove-InstalledCommands
    Remove-Item -LiteralPath $AppDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $AgyHome "ai-man-agy-credential.ps1") -Force -ErrorAction SilentlyContinue
    Write-Host "Uninstalled ai-man shims, app files, and managed helper."
    Write-Host "Profiles and credential backups were left in $AgyHome"
    exit 0
}

if ($Rollback) {
    $latestBackup = Get-LatestInstallBackup
    if (-not $latestBackup) {
        throw "no Windows app rollback backup found in $InstallRoot"
    }
    if (Test-Path -LiteralPath $AppDir) {
        Remove-Item -LiteralPath $AppDir -Recurse -Force
    }
    Move-Item -LiteralPath $latestBackup -Destination $AppDir
    Write-Host "Rolled back ai-man app files from $latestBackup to $AppDir"
}

$EntryPoint = if ($DevSource) { Join-Path $ProjectDir "profile_manager.py" } else { Join-Path $AppDir "profile_manager.py" }

if (-not $Rollback -and -not (Test-Path -LiteralPath $SourceEntryPoint)) {
    throw "profile_manager.py was not found next to install-windows.ps1"
}

function Copy-InstallSource([string]$SourceDir, [string]$DestinationDir) {
    $backupDir = $null
    if (Test-Path -LiteralPath $DestinationDir -PathType Container) {
        $backupDir = Get-InstallBackupDir
        Move-Item -LiteralPath $DestinationDir -Destination $backupDir
    }
    New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null

    foreach ($path in @("profile_manager.py", "README.md")) {
        $source = Join-Path $SourceDir $path
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $DestinationDir $path) -Force
        }
    }
    foreach ($dir in @("cli_profile_manager", "docs")) {
        $source = Join-Path $SourceDir $dir
        if (Test-Path -LiteralPath $source -PathType Container) {
            Copy-Item -LiteralPath $source -Destination (Join-Path $DestinationDir $dir) -Recurse -Force
        }
    }
    $scriptsSource = Join-Path $SourceDir "scripts"
    if (Test-Path -LiteralPath $scriptsSource -PathType Container) {
        $scriptsDest = Join-Path $DestinationDir "scripts"
        New-Item -ItemType Directory -Force -Path $scriptsDest | Out-Null
        Copy-Item -LiteralPath (Join-Path $scriptsSource "repair_windows_profile.ps1") -Destination $scriptsDest -Force -ErrorAction SilentlyContinue
        Copy-Item -LiteralPath (Join-Path $scriptsSource "verify_install_windows.ps1") -Destination $scriptsDest -Force -ErrorAction SilentlyContinue
    }
    if ($backupDir) {
        Write-Host "Previous app files backed up to $backupDir"
    }
}

if (-not $DevSource -and -not $Rollback) {
    Copy-InstallSource $ProjectDir $AppDir
}

if (-not (Test-Path -LiteralPath $EntryPoint -PathType Leaf)) {
    throw "installed entrypoint was not found: $EntryPoint"
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
