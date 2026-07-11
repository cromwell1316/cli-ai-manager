# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "config"
```

## Evidence

```bash
python3 -m py_compile cli_profile_manager/config.py cli_profile_manager/process_policy.py cli_profile_manager/operations.py cli_profile_manager/cli.py
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "config"
pytest -q tests/test_profile_manager.py tests/test_config_fast_path.py -k "not test_in_process_command_perf_budgets"
python3 scripts/benchmark_runtime.py --scenario commands
```

Results: H31 tests `4 passed`; existing config tests `6 passed, 170 deselected`;
broad suite `179 passed, 1 deselected`. In this run `config-json` median changed
from `129.546ms` before H31 to `93.310ms` after H31.
