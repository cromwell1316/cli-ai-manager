# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "config"
python3 scripts/benchmark_runtime.py --scenario command-execute
python3 scripts/benchmark_runtime.py --scenario commands
```

## Evidence

- Config JSON schema regression tests.
- Config command benchmark medians.
- Notes on unchanged health behavior.

## Results

```text
python3 -m pytest -q tests/test_config_fast_path.py tests/test_profile_manager.py -k "config"
14 passed, 184 deselected in 0.82s

python3 -m pytest -q
220 passed in 6.08s

python3 -m compileall -q cli_profile_manager
passed

python3 scripts/benchmark_runtime.py --scenario all
command-config-json median=2.031ms
config-json median=47.122ms
import-profile-manager median=29.648ms
```

The validation plan's `cold-subprocess` scenario name is not present in the
current benchmark CLI; `commands` is the available cold subprocess command
surface.
