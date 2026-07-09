# V_03 Command Perf Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- In-process `config show --json` stays within budget.
- In-process `list agy --json` stays within budget.
- In-process `status agy p1 --json` stays within budget.
- In-process `diagnostics agy --json` stays within budget.
- No deterministic perf test touches real tokens or native CLIs.

## Evidence

- `test_in_process_command_perf_budgets` covers `config show --json`,
  `list agy --json`, `status agy p1 --json`, and
  `diagnostics agy --json` with fake roots and no native CLI calls.
- `python3 scripts/benchmark_runtime.py --scenario command-execute --json`
  passed with medians:
  - `command-config-json`: `8.775ms`
  - `command-list-agy-json`: `4.919ms`
  - `command-status-agy-json`: `5.424ms`
  - `command-diagnostics-agy-json`: `5.454ms`
- `CommandSnapshot` reuses metadata, profile discovery, status, and AGY account
  lookup results within one command execution.
- Diagnostics accepts supplied profile indexes so command diagnostics does not
  repeat profile discovery already performed by the command snapshot.
