# H_02 Phase 02 JSON Baselines And Comparison

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Produce machine-readable benchmark output and compare it to stored baselines.

## Deliverables

- JSON benchmark output.
- Comparison command.
- Noise tolerance rules.
- Regression report format.

## Result

- Benchmark output includes `schema_version`, Python metadata, profile count,
  iterations, and named results.
- `--compare <baseline.json>` reports `comparisons`, `regressions`,
  `missing_current`, and `missing_baseline`.
- `--relative-tolerance` and `--absolute-tolerance-ms` control host-noise
  tolerance.
- `--write-baseline <path>` writes reviewable JSON baselines.
