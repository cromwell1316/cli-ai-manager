# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "diagnostics"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

## Evidence

- Fast diagnostics call guard results.
- Deep diagnostics payload compatibility results.
- Diagnostics benchmark median before and after implementation.

## Validation Results

```bash
pytest -q tests/test_config_fast_path.py
# 6 passed

pytest -q tests/test_profile_manager.py -k diagnostics
# 9 passed, 178 deselected

python3 scripts/benchmark_runtime.py --scenario command-execute
# command-diagnostics-agy-json median 65.947ms
```
