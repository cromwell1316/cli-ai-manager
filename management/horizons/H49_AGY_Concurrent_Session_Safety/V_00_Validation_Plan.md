# H49 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: validation

Status: planned.

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
ai-man launch agy p1
ai-man launch agy p2
```

```bash
python3 scripts/horizon_governance.py --json
```
