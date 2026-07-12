# H51 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate user-facing AGY credential recovery and backup commands.

## Checks

- Commands can save, set, clear, restore, and inspect managed backups.
- Sensitive values are redacted.
- Live Credential Manager mutations require confirmation.
- Invalid or missing backups return clear errors.

## Commands

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/cli.py cli_profile_manager/operations.py cli_profile_manager/diagnostics.py cli_profile_manager/safety.py cli_profile_manager/runtime_service.py
python3 -m pytest tests/test_profile_manager.py -k "credential or windows_agy or audit"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Completion Evidence

Validation covers command grammar, safety refusal/dry-run, token-safe backup
inspection, restore success, invalid backup failure, diagnostics, runtime
invalidation, governance, and the full suite.
