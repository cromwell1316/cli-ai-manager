# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --json
pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets
```

## Evidence

```bash
python3 -m py_compile scripts/benchmark_runtime.py
pytest -q tests/test_benchmark_guardrails.py
pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets
python3 scripts/benchmark_runtime.py --json --iterations 2
python3 scripts/benchmark_runtime.py --scenario all --iterations 5 --json --compare management/benchmark_baselines/local_default.json
```

Results: guardrail tests `4 passed`; perf budget test `1 passed`; full
benchmark comparison `ok: true` with `16` named sections and no regressions.
