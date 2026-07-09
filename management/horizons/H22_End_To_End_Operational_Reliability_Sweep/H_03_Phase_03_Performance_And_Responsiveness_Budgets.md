# H_03 Phase 03 Performance And Responsiveness Budgets

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Confirm that reliability features did not make the CLI slow or the interactive
experience sluggish.

## Scope

- Measure command startup and hot paths.
- Measure status/list with and without service.
- Measure quota parser and quota scheduler behavior.
- Measure audit write overhead for JSONL and SQLite.
- Measure interactive refresh smoothness and keyboard responsiveness.

## Acceptance

- Performance budgets are documented.
- Benchmark results are captured.
- Any regression has an owner and remediation plan.

## Evidence

Runtime benchmark command:

```bash
python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
```

Local benchmark summary:

| Scenario | Median |
| --- | ---: |
| python-startup | 14.484 ms |
| import-profile-manager | 27.385 ms |
| parse-args | 5.176 ms |
| command-config-json | 33.441 ms |
| command-list-agy-json | 5.537 ms |
| command-status-agy-json | 5.364 ms |
| command-diagnostics-agy-json | 81.079 ms |
| help | 43.755 ms |
| list-agy-json | 79.021 ms |
| diagnostics-agy-json | 218.450 ms |
| config-json | 140.400 ms |
| status-redraw | 0.466 ms |
| quota-parser | 0.138 ms |

No H22 performance blocker was identified in this run.
