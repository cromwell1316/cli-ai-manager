# H45 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Scope

Validate native Windows AGY quota probing without Unix PTY dependencies.

## Checks

- Windows AGY quota command construction uses the managed helper.
- Missing token returns `no_token` or `auth_required`.
- Missing PowerShell or AGY CLI returns actionable diagnostics.
- WSL/Linux quota behavior remains unchanged.

## Commands

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/cli.py cli_profile_manager/operations.py cli_profile_manager/quota.py
python3 -m pytest tests/test_profile_manager.py -k "quota or windows_agy"
python3 -m pytest
```
