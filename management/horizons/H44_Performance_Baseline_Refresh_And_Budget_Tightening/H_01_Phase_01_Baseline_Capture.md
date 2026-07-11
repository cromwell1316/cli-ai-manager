# H_01 Phase 01 Baseline Capture

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Capture representative benchmark results after the optimization horizons.

## Deliverables

- Full benchmark run with increased iterations.
- Median and spread notes for key scenarios.
- Identification of stable and noisy benchmark cases.
- Baseline evidence committed with the horizon.

## Implementation Notes

- Do not update budgets from a single noisy run.
- Keep environment assumptions documented.
- Compare both in-process and cold subprocess scenarios.

## Evidence

Environment:

- Python: 3.11.9
- Executable: `/home/olivercromwell/.pyenv/versions/3.11.9/bin/python3`
- Command: `python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json`

Two full benchmark captures were used before tightening budgets. Median results:

| Section | Run 1 | Run 2 | Baseline budget |
| --- | ---: | ---: | ---: |
| python-startup | 12.079ms | 11.931ms | 20.0ms |
| import-profile-manager | 32.490ms | 35.260ms | 50.0ms |
| parse-args | 6.693ms | 5.459ms | 12.0ms |
| command-config-json | 2.127ms | 2.452ms | 8.0ms |
| command-list-agy-json | 1.868ms | 1.422ms | 8.0ms |
| command-status-agy-json | 0.459ms | 0.441ms | 3.0ms |
| command-diagnostics-agy-json | 4.613ms | 4.142ms | 20.0ms |
| profile-index | 0.989ms | 1.193ms | 4.0ms |
| help | 42.549ms | 46.860ms | 70.0ms |
| list-agy-json | 71.068ms | 62.210ms | 150.0ms |
| diagnostics-agy-json | 89.080ms | 83.105ms | 130.0ms |
| config-json | 58.596ms | 54.199ms | 75.0ms |
| status-redraw | 0.014ms | 0.014ms | 1.0ms |
| quota-parser | 0.243ms | 0.235ms | 1.0ms |
| quota-cold-mock | 0.340ms | 0.316ms | 1.5ms |
| quota-warm-mock | 0.242ms | 0.235ms | 1.0ms |

Cold subprocess sections had low medians but occasional p95/max variance.
`list-agy-json` also showed contention sensitivity during validation, so its
budget was tightened from `180.0ms` to `150.0ms` instead of being anchored near
the best isolated medians.
