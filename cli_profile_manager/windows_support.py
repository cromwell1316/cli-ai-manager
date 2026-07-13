import os
import json
from pathlib import Path


HELPER_NAME = "ai-man-agy-credential.ps1"
AGY_SHARED_SLOT_TARGET = "gemini:antigravity"
AGY_SLOT_MUTEX_NAME = "Global\\ai-man-agy-credential-slot"


def powershell_executable(shutil_module):
    return (
        shutil_module.which("pwsh.exe")
        or shutil_module.which("powershell.exe")
        or shutil_module.which("pwsh")
        or shutil_module.which("powershell")
    )


def helper_path(base_dir):
    return os.path.join(str(base_dir), HELPER_NAME)


def agy_windows_credential_path(base_dir, profile_num):
    return os.path.join(str(base_dir), f"cred-p{int(profile_num)}.json")


def windows_agy_backup_state(base_dir, profile_num):
    path = agy_windows_credential_path(base_dir, profile_num)
    payload = {
        "profile": f"p{int(profile_num)}",
        "path": os.path.abspath(path),
        "exists": os.path.exists(path),
        "valid": False,
        "account": None,
        "saved_at": None,
        "blob_size": None,
        "error": None,
    }
    if not payload["exists"]:
        payload["error"] = "missing_backup"
        return payload
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if data.get("Target") and data.get("Target") != AGY_SHARED_SLOT_TARGET:
            payload["error"] = "unexpected_target"
            return payload
        blob = data.get("BlobBase64")
        if not blob:
            payload["error"] = "missing_blob"
            return payload
        payload.update({
            "valid": True,
            "account": data.get("Account"),
            "saved_at": data.get("SavedAt"),
            "blob_size": data.get("BlobSize"),
        })
    except Exception as exc:
        payload["error"] = str(exc).replace("BlobBase64", "credential blob")
    return payload


def windows_agy_live_slot_state(native_windows=False):
    return {
        "target": AGY_SHARED_SLOT_TARGET,
        "native_windows": bool(native_windows),
        "state": "not_inspected" if native_windows else "native_windows_only",
        "token_safe": True,
        "inspection": (
            "live slot is managed by the PowerShell helper immediately before launch/login"
            if native_windows
            else "live Credential Manager slot can only be inspected on native Windows"
        ),
    }


def windows_agy_session_state(base_dir, profile_num, login=False, native_windows=False):
    backup = windows_agy_backup_state(base_dir, profile_num)
    policy = windows_agy_concurrency_policy(native_windows=native_windows)
    action = "login" if login else "launch"
    ready = True
    blockers = []
    if not login and not backup["valid"]:
        ready = False
        blockers.append(f"valid Windows AGY backup is required before launch: {backup['error']}")
    return {
        "tool": "agy",
        "profile": f"p{int(profile_num)}",
        "action": action,
        "ready": ready,
        "blockers": blockers,
        "backup": backup,
        "live_slot": windows_agy_live_slot_state(native_windows=native_windows),
        "concurrency": policy,
        "recovery_commands": windows_agy_recovery_commands(f"p{int(profile_num)}"),
    }


def windows_agy_guardrail_lines(state):
    profile = state["profile"]
    action = state["action"]
    backup = state["backup"]
    lines = [
        "Native Windows AGY uses one shared Credential Manager slot per Windows user.",
        "ai-man serializes launch/login/set/save/clear for this Windows user; use separate Windows users for true parallel AGY isolation.",
    ]
    if action == "launch":
        if backup["valid"]:
            account = backup.get("account") or "(account unknown)"
            lines.append(f"Launching {profile} will restore its managed backup to the live slot: {account}.")
        else:
            lines.append(f"Cannot launch {profile}: valid managed backup is missing or invalid ({backup.get('error')}).")
    else:
        lines.append(f"Login for {profile} will clear the live slot first, then save a fresh cred-{profile}.json backup after AGY exits.")
    lock_timeout = os.environ.get("AI_MAN_AGY_SLOT_LOCK_TIMEOUT_SECONDS")
    if lock_timeout:
        lines.append(f"Shared-slot lock timeout: {lock_timeout}s.")
    return lines


def windows_agy_recovery_hint_lines(state):
    profile = state["profile"]
    return [
        f"Recovery for {profile}:",
        f"  ai-man login agy {profile}",
        f"  ai-man agy-credential restore <cred-backup.json> {profile} --dry-run --json",
        f"  ai-man agy-credential restore <cred-backup.json> {profile} --yes",
        f"  ai-man diagnostics agy --json --show-accounts",
    ]


def ensure_windows_agy_helper(base_dir):
    os.makedirs(base_dir, exist_ok=True)
    path = helper_path(base_dir)
    source = windows_agy_helper_source()
    current = None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            current = handle.read()
    except OSError:
        pass
    if current != source:
        tmp = f"{path}.tmp-{os.getpid()}"
        with open(tmp, "w", encoding="utf-8", newline="\r\n") as handle:
            handle.write(source)
        os.replace(tmp, path)
    return path


def windows_agy_launch_argv(powershell, helper, action, profile_num, base_dir, command, extra_args=None):
    argv = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        helper,
        "-Action",
        action,
        "-Profile",
        str(profile_num),
        "-BaseDir",
        str(Path(base_dir)),
        "-CommandPath",
        command,
        "-ToolArgsJson",
        json.dumps(list(extra_args or [])),
    ]
    return argv


def windows_agy_concurrency_policy(native_windows=False):
    return {
        "target": AGY_SHARED_SLOT_TARGET,
        "native_windows": bool(native_windows),
        "isolation": "shared_windows_user_slot",
        "policy": "serialized_shared_slot",
        "mutex": AGY_SLOT_MUTEX_NAME,
        "parallel_same_windows_user": "unsupported",
        "true_parallel_isolation": "use_separate_windows_users",
        "warning": (
            "Native Windows AGY uses one Credential Manager slot per Windows user; "
            "ai-man serializes AGY launches and login flows to avoid account crossover."
        ),
        "recovery": [
            "Close active native Windows AGY sessions for this Windows user.",
            "Run ai-man launch agy pN to restore the selected profile backup to the live slot.",
            "Use ai-man login agy pN if the selected backup must be refreshed.",
            "Use separate Windows users for true parallel native Windows AGY isolation.",
        ],
    }


def windows_agy_recovery_commands(profile="pN"):
    return [
        f"ai-man launch agy {profile}",
        f"ai-man login agy {profile}",
        "ai-man diagnostics agy --json --show-accounts",
    ]


def windows_agy_helper_source():
    return r'''# Managed by ai-man. Regenerated by install-windows.ps1 or Windows agy launch/login.
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Launch", "Login", "Set", "Save", "Clear", "Whoami")]
    [string]$Action,

    [int]$Profile = 0,
    [string]$BaseDir = (Join-Path $env:USERPROFILE "agy-homes"),
    [string]$CommandPath = "agy",
    [string]$ToolArgsJson = "[]"
)

$ErrorActionPreference = "Stop"
$TargetName = "gemini:antigravity"
$UserName = "antigravity"
$MutexName = "Global\ai-man-agy-credential-slot"
$LockTimeoutSeconds = 0
if ($env:AI_MAN_AGY_SLOT_LOCK_TIMEOUT_SECONDS) {
    try { $LockTimeoutSeconds = [int]$env:AI_MAN_AGY_SLOT_LOCK_TIMEOUT_SECONDS } catch { $LockTimeoutSeconds = 0 }
    if ($LockTimeoutSeconds -lt 0) { $LockTimeoutSeconds = 0 }
}
$ToolArgs = @()
if ($ToolArgsJson) {
    $parsedToolArgs = ConvertFrom-Json -InputObject $ToolArgsJson
    if ($null -ne $parsedToolArgs) {
        $ToolArgs = @($parsedToolArgs | ForEach-Object { [string]$_ })
    }
}

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public static class AiManCredNative {
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

function Get-ProfileHome([int]$N) {
    if ($N -le 0) { throw "Profile must be a positive pN number." }
    return Join-Path $BaseDir ("p{0}" -f $N)
}

function Get-CredPath([int]$N) {
    if ($N -le 0) { throw "Profile must be a positive pN number." }
    return Join-Path $BaseDir ("cred-p{0}.json" -f $N)
}

function Read-AgyWindowsCredentialFile([int]$N) {
    $path = Get-CredPath $N
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Missing Windows agy credential backup: $path"
    }
    $data = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($data.Target -and $data.Target -ne $TargetName) {
        throw "Unexpected credential target in $path`: $($data.Target)"
    }
    if (-not $data.BlobBase64) {
        throw "Credential backup is missing BlobBase64: $path"
    }
    return [Convert]::FromBase64String([string]$data.BlobBase64)
}

function Write-AgyCredentialBytes([byte[]]$Bytes) {
    if (-not $Bytes -or $Bytes.Length -eq 0) {
        throw "Credential blob is empty."
    }
    $ptr = [Runtime.InteropServices.Marshal]::AllocCoTaskMem($Bytes.Length)
    try {
        [Runtime.InteropServices.Marshal]::Copy($Bytes, 0, $ptr, $Bytes.Length)
        $cred = New-Object AiManCredNative+CREDENTIAL
        $cred.Type = 1
        $cred.TargetName = $TargetName
        $cred.CredentialBlobSize = $Bytes.Length
        $cred.CredentialBlob = $ptr
        $cred.Persist = 2
        $cred.UserName = $UserName
        if (-not [AiManCredNative]::CredWrite([ref]$cred, 0)) {
            $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
            throw "CredWrite failed with Win32 error $code"
        }
    } finally {
        if ($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::FreeCoTaskMem($ptr)
        }
    }
}

function Read-AgyCredentialBytes {
    $credPtr = [IntPtr]::Zero
    if (-not [AiManCredNative]::CredRead($TargetName, 1, 0, [ref]$credPtr)) {
        $code = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
        throw "CredRead failed with Win32 error $code"
    }
    try {
        $cred = [Runtime.InteropServices.Marshal]::PtrToStructure($credPtr, [type][AiManCredNative+CREDENTIAL])
        $bytes = New-Object byte[] $cred.CredentialBlobSize
        [Runtime.InteropServices.Marshal]::Copy($cred.CredentialBlob, $bytes, 0, $bytes.Length)
        return $bytes
    } finally {
        if ($credPtr -ne [IntPtr]::Zero) {
            [AiManCredNative]::CredFree($credPtr)
        }
    }
}

function Clear-AgyCredential {
    [void][AiManCredNative]::CredDelete($TargetName, 1, 0)
}

function Invoke-WithAgyCredentialSlotLock([scriptblock]$Body, [string]$Operation, [int]$N) {
    $mutex = New-Object System.Threading.Mutex($false, $MutexName)
    $acquired = $false
    try {
        $timeoutMs = $LockTimeoutSeconds * 1000
        $acquired = $mutex.WaitOne($timeoutMs)
        if (-not $acquired) {
            $profileText = if ($N -gt 0) { "p$N" } else { "the requested profile" }
            throw "Native Windows AGY is already using the shared Credential Manager slot '$TargetName' for this Windows user. Close the active AGY session, retry $Operation for $profileText, or use a separate Windows user for true parallel isolation."
        }
        & $Body
    } finally {
        if ($acquired) {
            try { $mutex.ReleaseMutex() | Out-Null } catch {}
        }
        $mutex.Dispose()
    }
}

function Set-AgyCredential([int]$N) {
    Write-AgyCredentialBytes (Read-AgyWindowsCredentialFile $N)
}

function Get-AgyAccount([int]$N) {
    $googleAccounts = Join-Path (Get-ProfileHome $N) ".gemini\google_accounts.json"
    if (Test-Path -LiteralPath $googleAccounts) {
        try {
            $data = Get-Content -LiteralPath $googleAccounts -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($data.active) { return ([string]$data.active).Trim().TrimEnd(",") }
        } catch {}
    }
    $credPath = Get-CredPath $N
    if (Test-Path -LiteralPath $credPath) {
        try {
            $data = Get-Content -LiteralPath $credPath -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($data.Account) { return ([string]$data.Account).Trim().TrimEnd(",") }
        } catch {}
    }
    return $null
}

function Save-AgyCredential([int]$N) {
    $bytes = Read-AgyCredentialBytes
    $path = Get-CredPath $N
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
    $payload = [ordered]@{
        Target = $TargetName
        Type = 1
        Persist = 2
        Flags = 0
        UserName = $UserName
        Account = Get-AgyAccount $N
        BlobBase64 = [Convert]::ToBase64String($bytes)
        BlobSize = $bytes.Length
        SavedAt = (Get-Date).ToString("o")
    }
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Invoke-AgyProfile([int]$N, [bool]$FreshLogin) {
    $operation = if ($FreshLogin) { "login" } else { "launch" }
    Invoke-WithAgyCredentialSlotLock {
        $profileHome = Get-ProfileHome $N
        New-Item -ItemType Directory -Force -Path $profileHome | Out-Null
        if ($FreshLogin) {
            Clear-AgyCredential
        } else {
            Set-AgyCredential $N
        }
        $oldUserProfile = $env:USERPROFILE
        $oldHome = $env:HOME
        try {
            $env:USERPROFILE = $profileHome
            $env:HOME = $profileHome
            & $CommandPath @ToolArgs
            $exitCode = $LASTEXITCODE
        } finally {
            $env:USERPROFILE = $oldUserProfile
            $env:HOME = $oldHome
        }
        if ($FreshLogin) {
            Save-AgyCredential $N | Out-Null
        }
        if ($null -ne $exitCode) { exit $exitCode }
    } $operation $N
}

switch ($Action) {
    "Launch" { Invoke-AgyProfile $Profile $false }
    "Login" { Invoke-AgyProfile $Profile $true }
    "Set" { Invoke-WithAgyCredentialSlotLock { Set-AgyCredential $Profile } "set" $Profile }
    "Save" { Invoke-WithAgyCredentialSlotLock { Save-AgyCredential $Profile | Write-Output } "save" $Profile }
    "Clear" { Invoke-WithAgyCredentialSlotLock { Clear-AgyCredential } "clear" $Profile }
    "Whoami" {
        Get-ChildItem -LiteralPath $BaseDir -Filter "cred-p*.json" -ErrorAction SilentlyContinue |
            Sort-Object Name |
            ForEach-Object {
                if ($_.BaseName -match "^cred-p(\d+)$") {
                    $n = [int]$Matches[1]
                    [pscustomobject]@{
                        Profile = "p$n"
                        Account = Get-AgyAccount $n
                        Credential = $_.FullName
                    }
                }
            } | Format-Table -AutoSize
    }
}
'''
