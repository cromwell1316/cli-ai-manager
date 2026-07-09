# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 profile_manager.py clear agy p1 --json
python3 profile_manager.py sync --json --dry-run
```

## Evidence Requirements

- Command inventory coverage.
- Dry-run and confirmation tests.
- Audit evidence for policy decisions.
- No-secret diagnostics evidence.
