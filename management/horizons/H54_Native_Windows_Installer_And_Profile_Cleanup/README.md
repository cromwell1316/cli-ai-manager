# H54 Native Windows Installer And Profile Cleanup

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make native Windows installation reliable even when old PowerShell profile
functions, broken Python launchers, or restrictive execution policies are
present.

## Goals

- Detect stale `ai-man`, `profile-man`, `pman`, `agy`, and `codex` functions in
  PowerShell profiles.
- Provide a safe profile cleanup command with dry-run output.
- Improve installer diagnostics for Python, PATH, helper freshness, and
  execution policy.
- Prefer Windows-local project paths for production installs while still
  supporting UNC development installs.
- Keep installer actions idempotent and reversible.

## Non-Goals

- Do not delete user profile content without explicit confirmation.
- Do not store secrets or tokens in installer logs.
- Do not require Administrator privileges.

## Phases

- Phase 01: profile conflict inventory and detection rules.
- Phase 02: dry-run cleanup and actionable diagnostics.
- Phase 03: installer integration and rollback path.
- Phase 04: Windows verification updates and docs.

## Verification

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man diagnostics --json
```

Acceptance target: a fresh or previously customized Windows PowerShell profile
can run `ai-man` without stale function conflicts or startup errors.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Profile_Conflict_Inventory.md`
- `H_02_Phase_02_Cleanup_Command_And_Dry_Run.md`
- `H_03_Phase_03_Installer_Integration.md`
- `H_04_Phase_04_Rollback_And_Runbook.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
