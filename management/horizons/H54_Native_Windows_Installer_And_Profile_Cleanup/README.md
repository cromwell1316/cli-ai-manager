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

- `README.md`

