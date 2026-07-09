# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/verify_no_tui_surface.sh
```

## Evidence Requirements

- Horizon structure check output.
- Evidence collection check output.
- README command example verification.
