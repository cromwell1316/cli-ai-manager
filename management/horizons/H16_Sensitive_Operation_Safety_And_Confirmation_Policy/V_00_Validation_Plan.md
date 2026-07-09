# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

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

## Evidence

- `python3 -m pytest -q` passed with H16 policy and command migration tests.
- `python3 profile_manager.py clear agy p1 --json` produced a structured
  confirmation refusal.
- Isolated `python3 profile_manager.py sync --json --dry-run` produced a
  structured dry-run with `safety` preflight.
