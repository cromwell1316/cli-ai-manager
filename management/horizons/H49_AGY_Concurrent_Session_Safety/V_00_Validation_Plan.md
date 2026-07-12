# H49 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate the operational safety model for concurrent native Windows AGY
sessions.

## Checks

- Staggered launches are tested with multiple profiles.
- Credential refresh behavior is observed and documented.
- Diagnostics can explain the active live slot when possible.
- User-facing warnings are present when concurrency is risky.

## Commands

```powershell
ai-man diagnostics agy --json --show-accounts
.\scripts\agy_windows_concurrency_drill.ps1
ai-man launch agy p1
ai-man launch agy p2
```

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows_agy or diagnostics"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Completion Evidence

Local automated validation covers the static helper mutex contract, diagnostics
policy payload, warning/audit path, and token redaction. Native live drill
commands remain explicit because they require real Windows AGY accounts.
