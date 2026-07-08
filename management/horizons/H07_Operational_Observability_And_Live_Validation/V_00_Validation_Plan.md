# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py
./scripts/verify_no_tui_surface.sh
```

## Manual Validation

```bash
python3 profile_manager.py diagnostics --json
python3 profile_manager.py diagnostics agy --json
```

If live validation script is implemented:

```bash
./scripts/validate_agy_quota_live.sh
```
