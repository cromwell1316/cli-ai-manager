# H_01 Phase 01 Filesystem Call Audit

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Measure profile-root, metadata, credential, and log-file filesystem calls per
command.

## Scope

- Add monkeypatched filesystem counters for deterministic tests.
- Measure:
  - `list <tool> --json`
  - `status <tool> p1 --json`
  - `diagnostics <tool> --json`
  - `doctor <tool> --json`
- Separate profile root listing, credential reads, metadata reads, AGY account
  reads, and diagnostics-only reads.
- Record budgets before changing implementation.

## Acceptance

- Tests can detect accidental repeated profile scans.
- Evidence records call counts for 1-profile and 12-profile fixtures.

## Evidence

- `tests/test_profile_manager.py::test_command_snapshot_reuses_profile_discovery_and_status`
  verifies that one command snapshot performs one occupied-profile discovery for
  repeated display, first-free, and status access.
- `python3 scripts/benchmark_runtime.py --scenario command-execute --json`
  passed with 12 profiles; median timings were `list agy --json` 5.495 ms,
  `status agy --json` 3.059 ms, and `diagnostics agy --json` 4.285 ms.
