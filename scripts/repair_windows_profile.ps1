param(
    [string[]]$ProfilePath,
    [string]$BinDir = (Join-Path $env:LOCALAPPDATA "Programs\ai-man\bin"),
    [switch]$Apply,
    [switch]$ConfirmCleanup,
    [string]$BackupDir
)

$ErrorActionPreference = "Stop"
$ManagedNames = @("ai-man", "profile-man", "pman", "agy", "codex")
$ManagedNamePattern = (($ManagedNames | ForEach-Object { [regex]::Escape($_) }) -join "|")
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

function Get-DefaultProfilePaths {
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

function Expand-ProfileString([string]$Value) {
    try {
        return $ExecutionContext.InvokeCommand.ExpandString($Value)
    } catch {
        return $Value
    }
}

function Get-MissingDotSourcePath([string]$Line) {
    if ($Line -match '^\s*\.\s+["'']([^"'']+)["'']') {
        $expanded = Expand-ProfileString $Matches[1]
        if ($expanded -and -not (Test-Path -LiteralPath $expanded)) {
            return $expanded
        }
    }
    return $null
}

function Get-FunctionBlockEnd([string[]]$Lines, [int]$StartIndex) {
    $depth = 0
    $seenBrace = $false
    for ($i = $StartIndex; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        foreach ($char in $line.ToCharArray()) {
            if ($char -eq "{") {
                $depth += 1
                $seenBrace = $true
            } elseif ($char -eq "}") {
                $depth -= 1
            }
        }
        if ($seenBrace -and $depth -le 0) {
            return $i
        }
    }
    return $StartIndex
}

function Find-ProfileIssues([string]$Path) {
    $issues = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $issues
    }

    $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        $lineNumber = $i + 1

        if ($line -match "^\s*function\s+($ManagedNamePattern)\b") {
            $end = Get-FunctionBlockEnd $lines $i
            $issues.Add([pscustomobject]@{
                Kind = "stale_function"
                Path = $Path
                Line = $lineNumber
                EndLine = $end + 1
                Name = $Matches[1]
                Message = "stale PowerShell function '$($Matches[1])' can shadow the installed ai-man shim"
            })
            $i = $end
            continue
        }

        if ($line -match "^\s*Set-Alias\s+($ManagedNamePattern)\b") {
            $issues.Add([pscustomobject]@{
                Kind = "stale_alias"
                Path = $Path
                Line = $lineNumber
                EndLine = $lineNumber
                Name = $Matches[1]
                Message = "stale PowerShell alias '$($Matches[1])' can shadow the installed ai-man shim"
            })
            continue
        }

        $missing = Get-MissingDotSourcePath $line
        if ($missing) {
            $issues.Add([pscustomobject]@{
                Kind = "missing_dot_source"
                Path = $Path
                Line = $lineNumber
                EndLine = $lineNumber
                Name = $missing
                Message = "dot-sourced file does not exist: $missing"
            })
            continue
        }

        if ($line -match "ai-man-tui-win|agy-multiaccount\.ps1|codex-multiaccount\.ps1") {
            $issues.Add([pscustomobject]@{
                Kind = "legacy_profile_reference"
                Path = $Path
                Line = $lineNumber
                EndLine = $lineNumber
                Name = "legacy"
                Message = "legacy ai-man/agy/codex profile reference should be guarded or removed"
            })
        }
    }
    return $issues
}

function Disable-IssueLines([string]$Path, [object[]]$Issues) {
    if (-not $Issues -or $Issues.Count -eq 0) {
        return $false
    }

    $resolvedBackupDir = $BackupDir
    if (-not $resolvedBackupDir) {
        $resolvedBackupDir = Split-Path -Parent $Path
    }
    New-Item -ItemType Directory -Force -Path $resolvedBackupDir | Out-Null
    $backup = Join-Path $resolvedBackupDir ("{0}.ai-man-backup-{1}" -f (Split-Path -Leaf $Path), $Timestamp)
    Copy-Item -LiteralPath $Path -Destination $backup -Force

    $lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
    $disable = @{}
    foreach ($issue in $Issues) {
        for ($lineNumber = [int]$issue.Line; $lineNumber -le [int]$issue.EndLine; $lineNumber++) {
            $disable[$lineNumber] = $issue.Message
        }
    }

    $updated = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $lineNumber = $i + 1
        if ($disable.ContainsKey($lineNumber) -and $lines[$i] -notmatch "^\s*#\s*ai-man cleanup disabled") {
            $updated.Add("# ai-man cleanup disabled $Timestamp: $($disable[$lineNumber])")
            $updated.Add("# $($lines[$i])")
        } else {
            $updated.Add($lines[$i])
        }
    }

    Set-Content -LiteralPath $Path -Value $updated -Encoding UTF8
    Write-Host "[OK] updated $Path"
    Write-Host "[OK] backup written to $backup"
    return $true
}

$paths = @($ProfilePath)
if (-not $paths -or $paths.Count -eq 0) {
    $paths = @(Get-DefaultProfilePaths)
}

$allIssues = New-Object System.Collections.Generic.List[object]
foreach ($path in $paths) {
    if (-not $path) { continue }
    $issues = @(Find-ProfileIssues $path)
    if ($issues.Count -eq 0) {
        Write-Host "[OK] no ai-man profile conflicts in $path"
        continue
    }
    foreach ($issue in $issues) {
        $allIssues.Add($issue)
        Write-Host "[ISSUE] $($issue.Path):$($issue.Line) $($issue.Message)"
    }
}

if ($allIssues.Count -eq 0) {
    exit 0
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run only. To apply:"
    Write-Host ".\scripts\repair_windows_profile.ps1 -Apply -ConfirmCleanup"
    exit 0
}

if (-not $ConfirmCleanup) {
    throw "Refusing to edit profile files without -ConfirmCleanup"
}

foreach ($path in ($allIssues | Select-Object -ExpandProperty Path -Unique)) {
    $issues = @($allIssues | Where-Object { $_.Path -eq $path })
    [void](Disable-IssueLines $path $issues)
}
