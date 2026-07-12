# H55 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate native Windows AGY shared-slot messaging, lock behavior, recovery
guidance, and token-safe diagnostics.

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "agy and windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Evidence

- Launch/login flows explain serialized shared-slot behavior.
- Recovery paths identify missing backups, stale live slots, and lock contention.
- Tests do not expose real credential blobs.
- Direct CLI blocks missing-backup launch before invoking PowerShell.
