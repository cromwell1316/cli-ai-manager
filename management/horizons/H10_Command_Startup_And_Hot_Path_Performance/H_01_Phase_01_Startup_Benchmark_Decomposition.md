# H_01 Phase 01 Startup Benchmark Decomposition

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Extend runtime benchmarks so startup cost is visible as separate, comparable
phases.

## Scope

- Add benchmark scenarios for:
  - `python-startup`: minimal `python3 --version` or `python3 -c pass`.
  - `import-profile-manager`: import package and entrypoint without running a
    command.
  - `parse-args`: build parser and parse representative arguments.
  - `command-execute`: run command handlers in-process with fake profile roots.
- Report subprocess and in-process measurements separately.
- Record current host startup overhead in validation evidence.
- Avoid real tokens and live quota probes.

## Acceptance

- `scripts/benchmark_runtime.py` exposes the new scenarios.
- JSON benchmark output includes phase names and enough metadata to compare
  cold/warm runs.
- The validation notes distinguish host Python startup from application work.
