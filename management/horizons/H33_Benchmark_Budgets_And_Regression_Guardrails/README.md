# H33 Benchmark Budgets And Regression Guardrails

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Turn performance expectations into stable regression checks instead of ad hoc
manual measurements.

## Goals

- Maintain repeatable benchmarks for startup, imports, commands, rendering, and
  quota parsing.
- Separate in-process budgets from subprocess budgets.
- Store baseline output in a machine-readable form.
- Reduce test flakiness by avoiding noisy wall-clock thresholds where possible.
- Make regressions actionable by naming the slow section.

## Non-Goals

- Do not require live AGY/Codex/Claude tokens for normal performance tests.
- Do not fail CI on host-specific Python startup noise without tolerance.
- Do not add external telemetry.

## Work Areas

- Extend `scripts/benchmark_runtime.py` with JSON output.
- Add benchmark comparison mode.
- Track import count and import time separately.
- Add fake filesystem fixtures for profile index benchmarks.
- Add warm/cold quota mock benchmarks.

## Validation

```bash
python3 scripts/benchmark_runtime.py --json
pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets
```

Acceptance target: performance changes are measurable, reviewable, and guarded
by stable local tests.

## Implementation Notes

- Benchmark JSON now uses schema version 2 and includes Python runtime metadata.
- `scripts/benchmark_runtime.py` can compare current results with a baseline via
  `--compare`, using relative and absolute tolerances.
- `--write-baseline` writes reviewable machine-readable benchmark output.
- The default local baseline lives at
  `management/benchmark_baselines/local_default.json`.
- Added repeatable fake-token surfaces for profile index and cold/warm quota
  mock paths.
- Import timing now reports `module_count` separately from elapsed time.

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

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Benchmark_Surface_Inventory.md`
- `H_02_Phase_02_JSON_Baselines_And_Comparison.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
