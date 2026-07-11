# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Baseline | Fresh full benchmark results are recorded | Two `all --iterations 20 --json` runs |
| Budgets | Only stable scenarios are tightened | `local_default.json` and in-process budget diff |
| Guardrails | Benchmark tests pass after updates | Guardrail test output |
| Stability | Noisy scenarios are documented instead of over-tightened | Cold subprocess notes in phase evidence |
