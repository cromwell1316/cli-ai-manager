# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "config"
```

## Evidence

- Config timing before/after.
- JSON compatibility sample.
