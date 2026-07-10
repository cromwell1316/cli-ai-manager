# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --json
pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets
```

## Evidence

- Baseline JSON.
- Regression report example.
