# H51 Credential Recovery And Backup UX

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Improve user-facing recovery and backup workflows around Windows AGY
Credential Manager switching.

## Goals

- Add explicit commands for saving, setting, clearing, and restoring AGY
  Windows credential backups.
- Provide a safe path to restore `cred-backup.json` or a selected `cred-pN.json`
  into the live Credential Manager slot.
- Add `whoami` style diagnostics for managed AGY backups.
- Keep token values redacted in all output.
- Add confirmation policy for live Credential Manager mutations.

## Non-Goals

- Do not print raw OAuth tokens.
- Do not delete backups without explicit confirmation.
- Do not invent a new credential storage format.

## Work Areas

- Design command grammar for AGY credential recovery operations.
- Route commands through the existing safety/audit framework.
- Extend the PowerShell helper actions if needed.
- Add tests for success, missing backup, invalid backup, and dry-run behavior.

## Validation

```bash
python3 -m pytest tests/test_profile_manager.py -k "credential or windows_agy or audit"
python3 -m pytest
```

Acceptance target: users can inspect and restore Windows AGY credential state
without manually editing PowerShell scripts or exposing token blobs.

## Files

- `README.md`
