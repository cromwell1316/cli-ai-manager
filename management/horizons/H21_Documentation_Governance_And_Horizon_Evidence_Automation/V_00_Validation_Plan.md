# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/horizon_governance.py --json
python3 scripts/horizon_governance.py --horizon management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation --evidence --write --json
bash scripts/verify_no_tui_surface.sh
```

## Evidence Requirements

- Horizon structure check output.
- Evidence collection check output.
- README command example verification.

## Result

- `python3 -m pytest -q`: 118 passed.
- `python3 scripts/horizon_governance.py --json`: ok.
- `python3 scripts/horizon_governance.py --horizon management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation --evidence --write --json`: ok.
- `bash scripts/verify_no_tui_surface.sh`: ok.
