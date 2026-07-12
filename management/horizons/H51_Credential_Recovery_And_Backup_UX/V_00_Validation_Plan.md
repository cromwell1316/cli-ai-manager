# H51 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Scope

Validate user-facing AGY credential recovery and backup commands.

## Checks

- Commands can save, set, clear, restore, and inspect managed backups.
- Sensitive values are redacted.
- Live Credential Manager mutations require confirmation.
- Invalid or missing backups return clear errors.

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "credential or windows_agy or audit"
python3 -m pytest
```
