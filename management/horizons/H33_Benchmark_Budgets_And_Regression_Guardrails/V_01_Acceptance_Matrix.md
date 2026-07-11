# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Area | Acceptance |
| --- | --- |
| Repeatability | Benchmarks run without live CLI tokens |
| Signal | Reports name the regressed section |
| Stability | Budgets tolerate normal host noise |
| Review | Baseline changes are easy to inspect |

## Result

| Area | Result |
| --- | --- |
| Repeatability | All benchmark surfaces use fake profiles, fake quota samples, or no token state |
| Signal | Comparison reports include named `regressions` with current, baseline, delta, ratio, and threshold |
| Stability | Relative and absolute tolerances are configurable; default local baseline is intentionally host-tolerant |
| Review | Baselines are plain JSON and can be refreshed with `--write-baseline` |
