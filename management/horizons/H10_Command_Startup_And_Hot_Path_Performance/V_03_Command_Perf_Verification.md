# V_03 Command Perf Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Checks

- In-process `config show --json` stays within budget.
- In-process `list agy --json` stays within budget.
- In-process `status agy p1 --json` stays within budget.
- In-process `diagnostics agy --json` stays within budget.
- No deterministic perf test touches real tokens or native CLIs.

## Evidence

Pending implementation.
