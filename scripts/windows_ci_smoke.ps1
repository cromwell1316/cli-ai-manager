param(
    [string]$BinDir = (Join-Path $env:TEMP "ai-man-ci-bin"),
    [string]$AgyHome = (Join-Path $env:TEMP "ai-man-ci-agy-homes"),
    [switch]$SkipPytest
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

function Invoke-Step([string]$Name, [scriptblock]$Body) {
    Write-Host ""
    Write-Host "==> $Name"
    & $Body
}

Push-Location $ProjectDir
try {
    Invoke-Step "Python syntax smoke" {
        python -m py_compile `
            profile_manager.py `
            cli_profile_manager\cli.py `
            cli_profile_manager\operations.py `
            cli_profile_manager\windows_support.py `
            cli_profile_manager\diagnostics.py
    }

    if (-not $SkipPytest) {
        Invoke-Step "Focused Windows pytest smoke" {
            python -m pytest tests\test_profile_manager.py -k "windows"
        }
    }

    Invoke-Step "Install into temporary Windows paths" {
        if (Test-Path -LiteralPath $BinDir) {
            Remove-Item -LiteralPath $BinDir -Recurse -Force
        }
        if (Test-Path -LiteralPath $AgyHome) {
            Remove-Item -LiteralPath $AgyHome -Recurse -Force
        }
        .\install-windows.ps1 -BinDir $BinDir -AgyHome $AgyHome -NoPathUpdate
    }

    Invoke-Step "Verify temporary install without PATH or Credential Manager mutation" {
        .\scripts\verify_install_windows.ps1 `
            -BinDir $BinDir `
            -AgyHome $AgyHome `
            -SkipPathCheck `
            -SkipCredentialCheck
    }

    Invoke-Step "Static helper contract" {
        $helper = Join-Path $AgyHome "ai-man-agy-credential.ps1"
        $text = Get-Content -LiteralPath $helper -Raw -Encoding UTF8
        foreach ($needle in @(
            "gemini:antigravity",
            "CredWrite",
            "CredRead",
            "Global\ai-man-agy-credential-slot",
            "Invoke-WithAgyCredentialSlotLock"
        )) {
            if ($text -notlike "*$needle*") {
                throw "installed helper is missing expected text: $needle"
            }
        }
        Write-Host "helper contract passed"
    }

    Invoke-Step "Horizon governance" {
        python scripts\horizon_governance.py --json
    }
} finally {
    Pop-Location
}
