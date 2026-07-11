# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or tmux"
python3 scripts/benchmark_runtime.py --scenario quota-parser
```

## Live Validation

```bash
python3 scripts/validate_agy_quota_live.py --dry-run
```

## Evidence

```bash
python3 -m py_compile cli_profile_manager/quota.py
pytest -q tests/test_quota_warm_path.py
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py -k "quota or tmux"
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py -k "not test_in_process_command_perf_budgets"
python3 scripts/benchmark_runtime.py --scenario quota-parser
python3 scripts/validate_agy_quota_live.py --dry-run
```

Results: H29 tests `4 passed`; quota/tmux suite `85 passed, 93 deselected`;
broad suite `177 passed, 1 deselected`; quota parser benchmark median
`0.230ms`, p95 `0.307ms`.
