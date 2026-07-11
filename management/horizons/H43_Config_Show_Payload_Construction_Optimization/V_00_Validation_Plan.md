# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "config"
python3 scripts/benchmark_runtime.py --scenario command-execute
python3 scripts/benchmark_runtime.py --scenario cold-subprocess
```

## Evidence

- Config JSON schema regression tests.
- Config command benchmark medians.
- Notes on unchanged health behavior.
