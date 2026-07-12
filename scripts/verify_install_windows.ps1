param(
    [string]$BinDir = (Join-Path $env:LOCALAPPDATA "Programs\ai-man\bin"),
    [string]$AgyHome = (Join-Path $env:USERPROFILE "agy-homes"),
    [switch]$SkipPathCheck,
    [switch]$SkipCredentialCheck
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$EntryPoint = Join-Path $ProjectDir "profile_manager.py"
$HelperPath = Join-Path $AgyHome "ai-man-agy-credential.ps1"
$Commands = @("ai-man", "profile-man", "pman")
$Failures = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

function Write-Ok([string]$Message) {
    Write-Host "[OK] $Message"
}

function Write-Warn([string]$Message) {
    $script:Warnings.Add($Message)
    Write-Host "[WARN] $Message"
}

function Write-Fail([string]$Message) {
    $script:Failures.Add($Message)
    Write-Host "[FAIL] $Message"
}

function Test-ContainsPath([string]$PathValue, [string]$Expected) {
    if (-not $PathValue) { return $false }
    $expectedFull = [System.IO.Path]::GetFullPath($Expected).TrimEnd("\")
    foreach ($part in ($PathValue -split ";")) {
        if (-not $part) { continue }
        try {
            $partFull = [System.IO.Path]::GetFullPath($part).TrimEnd("\")
            if ([string]::Equals($partFull, $expectedFull, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        } catch {}
    }
    return $false
}

function Invoke-Python([object]$Python, [string[]]$Arguments) {
    $allArgs = @($Python.Args) + $Arguments
    & $Python.Source @allArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
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

function Test-Shim([string]$Name) {
    $ps1 = Join-Path $BinDir "$Name.ps1"
    $cmd = Join-Path $BinDir "$Name.cmd"
    $ok = $true

    if (-not (Test-Path -LiteralPath $ps1 -PathType Leaf)) {
        Write-Fail "missing PowerShell shim: $ps1"
        $ok = $false
    }
    if (-not (Test-Path -LiteralPath $cmd -PathType Leaf)) {
        Write-Fail "missing CMD shim: $cmd"
        $ok = $false
    }
    if ($ok) {
        $ps1Text = Get-Content -LiteralPath $ps1 -Raw -Encoding UTF8
        $cmdText = Get-Content -LiteralPath $cmd -Raw -Encoding UTF8
        if ($ps1Text -notlike "*$EntryPoint*" -or $cmdText -notlike "*$EntryPoint*") {
            Write-Fail "$Name shims do not point at $EntryPoint"
            return
        }
        Write-Ok "$Name shims point at $EntryPoint"
    }
}

function Test-HelperFreshness([object]$Python) {
    if (-not (Test-Path -LiteralPath $HelperPath -PathType Leaf)) {
        Write-Fail "missing AGY Credential Manager helper: $HelperPath"
        return
    }

    $expectedPath = [System.IO.Path]::GetTempFileName()
    try {
        Push-Location $ProjectDir
        try {
            Invoke-Python $Python @(
                "-c",
                "from pathlib import Path; import sys; from cli_profile_manager.windows_support import windows_agy_helper_source; Path(sys.argv[1]).write_text(windows_agy_helper_source(), encoding='utf-8', newline='')",
                $expectedPath
            )
        } finally {
            Pop-Location
        }
        $expected = Get-Content -LiteralPath $expectedPath -Raw -Encoding UTF8
    } finally {
        Remove-Item -LiteralPath $expectedPath -Force -ErrorAction SilentlyContinue
    }
    $current = Get-Content -LiteralPath $HelperPath -Raw -Encoding UTF8
    if (($current -replace "`r`n", "`n") -ne ($expected -replace "`r`n", "`n")) {
        Write-Fail "AGY helper is stale; rerun .\install-windows.ps1"
        return
    }
    Write-Ok "AGY Credential Manager helper is present and current"
}

function Test-CredentialManagerAccess {
    $target = "ai-man-install-verify-$PID-$([guid]::NewGuid().ToString('N'))"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes("ai-man verify")
    $ptr = [Runtime.InteropServices.Marshal]::AllocCoTaskMem($bytes.Length)
    $credPtr = [IntPtr]::Zero

    if (-not ("AiManInstallVerifyCredNative" -as [type])) {
        Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class AiManInstallVerifyCredNative {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREDENTIAL {
        public UInt32 Flags;
        public UInt32 Type;
        public string TargetName;
        public string Comment;
        public System.Runtime.InteropServices.ComTypes.FILETIME LastWritten;
        public UInt32 CredentialBlobSize;
        public IntPtr CredentialBlob;
        public UInt32 Persist;
        public UInt32 AttributeCount;
        public IntPtr Attributes;
        public string TargetAlias;
        public string UserName;
    }

    [DllImport("Advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CredWrite([In] ref CREDENTIAL userCredential, UInt32 flags);

    [DllImport("Advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CredRead(string target, UInt32 type, UInt32 flags, out IntPtr credentialPtr);

    [DllImport("Advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CredDelete(string target, UInt32 type, UInt32 flags);

    [DllImport("Advapi32.dll", SetLastError = true)]
    public static extern void CredFree(IntPtr buffer);
}
"@
    }

    try {
        [Runtime.InteropServices.Marshal]::Copy($bytes, 0, $ptr, $bytes.Length)
        $cred = New-Object AiManInstallVerifyCredNative+CREDENTIAL
        $cred.Type = 1
        $cred.TargetName = $target
        $cred.CredentialBlobSize = $bytes.Length
        $cred.CredentialBlob = $ptr
        $cred.Persist = 2
        $cred.UserName = "ai-man-install-verify"
        if (-not [AiManInstallVerifyCredNative]::CredWrite([ref]$cred, 0)) {
            $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            throw "CredWrite failed with Win32 error $code"
        }
        if (-not [AiManInstallVerifyCredNative]::CredRead($target, 1, 0, [ref]$credPtr)) {
            $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            throw "CredRead failed with Win32 error $code"
        }
        Write-Ok "Credential Manager read/write/delete check passed with temporary target"
    } finally {
        if ($credPtr -ne [IntPtr]::Zero) {
            [AiManInstallVerifyCredNative]::CredFree($credPtr)
        }
        [void][AiManInstallVerifyCredNative]::CredDelete($target, 1, 0)
        if ($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::FreeCoTaskMem($ptr)
        }
    }
}

Write-Host "Verifying ai-man Windows install"
Write-Host "Project: $ProjectDir"
Write-Host "BinDir:  $BinDir"
Write-Host "AgyHome: $AgyHome"

if (Test-Path -LiteralPath $EntryPoint -PathType Leaf) {
    Write-Ok "entrypoint exists: $EntryPoint"
} else {
    Write-Fail "missing entrypoint: $EntryPoint"
}

$python = Find-Python
if ($python) {
    try {
        $version = Invoke-Python $python @("--version")
        Write-Ok "Python is available: $($python.Source) $version"
    } catch {
        Write-Fail "Python was found but could not run: $($_.Exception.Message)"
    }
} else {
    Write-Fail "Python 3 was not found in PATH. Install Python or open a shell where py.exe/python.exe is available."
}

$pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
$powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
if ($PSVersionTable -or $pwsh -or $powershell) {
    Write-Ok "PowerShell is available"
} else {
    Write-Fail "PowerShell was not found"
}

if (Test-Path -LiteralPath $BinDir -PathType Container) {
    Write-Ok "shim directory exists"
    foreach ($name in $Commands) {
        Test-Shim $name
    }
} else {
    Write-Fail "missing shim directory: $BinDir"
}

if (-not $SkipPathCheck) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (Test-ContainsPath $userPath $BinDir) {
        Write-Ok "user Path contains shim directory"
    } else {
        Write-Fail "user Path does not contain $BinDir; rerun .\install-windows.ps1 or pass -SkipPathCheck"
    }

    if (Test-ContainsPath $env:Path $BinDir) {
        Write-Ok "current shell PATH contains shim directory"
    } else {
        Write-Warn "current shell PATH does not contain $BinDir; open a new PowerShell window"
    }
} else {
    Write-Warn "PATH check skipped by -SkipPathCheck"
}

if ($python) {
    try {
        Test-HelperFreshness $python
    } catch {
        Write-Fail "AGY helper verification failed: $($_.Exception.Message)"
    }
}

if (-not $SkipCredentialCheck) {
    try {
        Test-CredentialManagerAccess
    } catch {
        Write-Fail "Credential Manager check failed: $($_.Exception.Message)"
    }
} else {
    Write-Warn "Credential Manager check skipped by -SkipCredentialCheck"
}

if ($Failures.Count -gt 0) {
    Write-Host ""
    Write-Host "install verification failed:"
    foreach ($failure in $Failures) {
        Write-Host "  - $failure"
    }
    exit 1
}

Write-Host ""
Write-Host "install verification passed"
if ($Warnings.Count -gt 0) {
    Write-Host "warnings:"
    foreach ($warning in $Warnings) {
        Write-Host "  - $warning"
    }
}
