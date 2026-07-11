# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
pytest -q tests/test_benchmark_guardrails.py
pytest -q
```

## Evidence

- Full benchmark JSON output.
- Budget threshold diff and rationale.
- Guardrail test result.

## Results

- Fresh full benchmark was captured twice with `--scenario all --iterations 20
  --json`.
- Baseline medians were tightened in `management/benchmark_baselines/local_default.json`.
- In-process command budgets were tightened in
  `tests/test_profile_manager.py::test_in_process_command_perf_budgets`.
- Cold subprocess paths were kept intentionally looser than measured medians due
  to interpreter startup, host filesystem variance, and observed contention in
  `list-agy-json`.
- Final validation:
  - `python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
    --compare management/benchmark_baselines/local_default.json`: passed.
  - `python3 -m pytest -q tests/test_benchmark_guardrails.py
    tests/test_profile_manager.py::test_in_process_command_perf_budgets`: `5`
    passed.
  - `python3 -m pytest -q`: `220` passed.
  - `python3 -m compileall -q cli_profile_manager scripts profile_manager.py`:
    passed.
