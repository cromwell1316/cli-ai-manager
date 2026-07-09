# H_03 Phase 03 In Process Command Perf Harness

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Add deterministic performance tests for command handlers without subprocess
startup noise.

## Scope

- Add helper fixtures that create fake profile roots, metadata, labels, and
  credential files.
- Invoke command handlers or parser dispatch in-process.
- Capture stdout/stderr without touching real profile directories.
- Measure representative commands:
  - `config show --json`
  - `list agy --json`
  - `status agy p1 --json`
  - `diagnostics agy --json`
- Add budget assertions with enough slack for local development variance.

## Acceptance

- Perf tests run under `pytest` without network, native CLIs, or real tokens.
- Budgets fail on accidental repeated scans or heavyweight imports in hot paths.
- Tests report useful failure context instead of only a raw timeout.
