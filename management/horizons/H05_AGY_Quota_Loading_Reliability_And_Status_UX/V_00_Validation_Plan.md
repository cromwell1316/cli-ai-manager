# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Commands

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py
python3 -m pytest -q
./scripts/verify_no_tui_surface.sh
python3 profile_manager.py quota agy p1 --json --timeout 60
python3 profile_manager.py status agy p1 --json --quota --timeout 60
```

The real AGY commands are manual validation commands. Automated tests must not
depend on live credentials or network availability.

## Evidence Required

- Pytest includes deterministic scheduler tests.
- Pytest includes persistent session reuse/restart tests.
- Pytest includes stale-cache and diagnostic preservation tests.
- Pytest includes AGY quota-column rendering tests.
- Manual AGY validation shows at least two profiles eventually populate quota
  columns without causing every row to become `retry`.
- Reopening AGY status in the same manager process shows cached values before
  refresh completion.
