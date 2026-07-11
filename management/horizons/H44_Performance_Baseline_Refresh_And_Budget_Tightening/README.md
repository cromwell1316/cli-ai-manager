# H44 Performance Baseline Refresh And Budget Tightening

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Refresh performance baselines after the optimization horizons and tighten
budgets around the new measured steady state.

## Goals

- Capture fresh benchmark baselines on the current implementation.
- Tighten only budgets that have stable measured headroom.
- Keep budget checks useful without making them flaky.
- Document residual slow paths for future horizons.

## Non-Goals

- Do not tighten budgets before optimization work lands.
- Do not hide regressions by broadening thresholds.
- Do not add new product behavior.

## Work Areas

- Run benchmark suites with enough iterations for stable medians.
- Compare new medians against current budgets.
- Update budget thresholds only where evidence supports it.
- Add notes for any scenario left intentionally unchanged.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
pytest -q tests/test_benchmark_guardrails.py
pytest -q
```

Acceptance target: benchmark guardrails reflect the optimized steady state and
continue to catch meaningful regressions.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Baseline_Capture.md`
- `H_02_Phase_02_Budget_Tightening_And_Evidence.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
