# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or tmux"
python3 scripts/benchmark_runtime.py --scenario quota-parser
```

## Live Validation

```bash
python3 scripts/validate_agy_quota_live.py --dry-run
```
