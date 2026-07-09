# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/benchmark_runtime.py --scenario quota-parser --iterations 100 --json
python3 profile_manager.py diagnostics agy --json
```

## Optional Manual Validation

```bash
python3 profile_manager.py quota agy p1 --json
AI_MAN_INTERACTIVE_QUOTA=1 python3 profile_manager.py
```

## Evidence Requirements

- Fake AGY CLI proves controlling-terminal launch.
- Fake AGY CLI proves readiness-gated `/usage` delivery.
- Failure classification tests cover auth, ineligible account, resource
  exhaustion, timeout, parser miss, and process exit.
- Interactive status no longer shows `!` for every valid AGY account solely due
  to startup wrapper behavior.
- Diagnostics and audit include sanitized failure reasons.
