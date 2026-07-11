# H_02 Phase 02 Budget Tightening And Evidence

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Update benchmark budgets only where the new baseline has stable headroom.

## Deliverables

- Budget updates for stable improved scenarios.
- Rationale for unchanged or loose budgets.
- Guardrail test run.
- Final benchmark evidence in validation notes.

## Implementation Notes

- Prefer conservative thresholds over flaky checks.
- Do not broaden budgets to hide regressions.
- Keep benchmark guardrail tests readable.

## Budget Changes

- `local_default.json` medians were tightened for all benchmark sections.
- `test_in_process_command_perf_budgets` now uses:
  - `config show --json`: `12.0ms`
  - `list agy --json`: `12.0ms`
  - `status agy p1 --json`: `6.0ms`
  - `diagnostics agy --json`: `35.0ms`
- No budget was broadened.

## Validation Evidence

- `python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json`
  completed twice before updating thresholds.
- `python3 -m pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets`
  passed before tightening from the old loose values.
- `python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
  --compare management/benchmark_baselines/local_default.json` passed after
  budget updates.
- `python3 -m pytest -q tests/test_benchmark_guardrails.py
  tests/test_profile_manager.py::test_in_process_command_perf_budgets` passed.
- `python3 -m pytest -q` passed with `220` tests.
- `python3 -m compileall -q cli_profile_manager scripts profile_manager.py`
  passed.
