param(
    [string[]]$Profiles = @("p1", "p2", "p3"),
    [int]$StaggerSeconds = 5,
    [switch]$Run
)

$ErrorActionPreference = "Stop"

Write-Host "AGY Windows concurrency drill"
Write-Host "Policy: native Windows AGY uses one Credential Manager slot per Windows user."
Write-Host "Expected ai-man behavior: serialized_shared_slot; concurrent launches in one Windows user are unsupported."
Write-Host ""
Write-Host "Profiles: $($Profiles -join ', ')"
Write-Host "Stagger: $StaggerSeconds seconds"
Write-Host ""

Write-Host "Preflight diagnostics:"
Write-Host "  ai-man diagnostics agy --json --show-accounts"
Write-Host ""
Write-Host "Recovery commands:"
foreach ($profile in $Profiles) {
    Write-Host "  ai-man launch agy $profile"
    Write-Host "  ai-man login agy $profile"
}
Write-Host ""

if (-not $Run) {
    Write-Host "Dry run only. Pass -Run to start staggered ai-man launch commands."
    exit 0
}

$jobs = @()
foreach ($profile in $Profiles) {
    Write-Host "Starting ai-man launch agy $profile"
    $jobs += Start-Job -ScriptBlock {
        param($Profile)
        ai-man launch agy $Profile
    } -ArgumentList $profile
    Start-Sleep -Seconds $StaggerSeconds
}

Write-Host ""
Write-Host "Waiting for launched jobs. Close AGY windows to complete the drill."
Wait-Job -Job $jobs | Out-Null
Receive-Job -Job $jobs
Remove-Job -Job $jobs
