# H33 Benchmark Budgets And Regression Guardrails

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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
