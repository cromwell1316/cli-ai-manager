# H_01 Phase 01 Benchmark Surface Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H33_Benchmark_Budgets_And_Regression_Guardrails/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Define the benchmark surfaces that matter for everyday use.

## Deliverables

- Startup benchmark set.
- In-process command benchmark set.
- Render and parser benchmark set.
- Warm/cold quota benchmark plan.

## Result

- Startup/import surfaces: `python-startup`, `import-profile-manager`.
- In-process command surfaces: `command-config-json`, `command-list-agy-json`,
  `command-status-agy-json`, `command-diagnostics-agy-json`.
- Subprocess command surfaces: `help`, `list-agy-json`,
  `diagnostics-agy-json`, `config-json`.
- Render/parser surfaces: `status-redraw`, `quota-parser`.
- Fake filesystem and quota surfaces: `profile-index`, `quota-cold-mock`,
  `quota-warm-mock`.
