# H51 Credential Recovery And Backup UX

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

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

## Implementation Evidence

- Added `ai-man agy-credential` subcommands: `whoami`, `restore`, `set`, `save`,
  and `clear`.
- Mutating recovery actions require `--yes` and support `--dry-run` preflight.
- Recovery operations validate Windows AGY backups before writing managed
  `cred-pN.json` files or calling the native helper.
- Diagnostics now include token-safe `agy_credential_recovery` backup summaries.
- Tests cover token-safe inspection, restore dry-run/apply, invalid backups,
  confirmation refusal, live-slot dry-run, safety inventory, and runtime-service
  invalidation.

## Validation

```bash
python3 -m pytest tests/test_profile_manager.py -k "credential or windows_agy or audit"
python3 -m pytest
```

Acceptance target: users can inspect and restore Windows AGY credential state
without manually editing PowerShell scripts or exposing token blobs.

Completed validation:

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/cli.py cli_profile_manager/operations.py cli_profile_manager/diagnostics.py cli_profile_manager/safety.py cli_profile_manager/runtime_service.py
python3 -m pytest tests/test_profile_manager.py -k "credential or windows_agy or audit"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Command_Grammar_And_Safety_Model.md`
- `H_02_Phase_02_Helper_And_Operations_Integration.md`
- `H_03_Phase_03_Diagnostics_And_Runbook.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
