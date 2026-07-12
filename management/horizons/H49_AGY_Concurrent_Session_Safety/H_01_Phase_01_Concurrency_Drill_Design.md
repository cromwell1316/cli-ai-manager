# H_01 Phase 01 Concurrency Drill Design

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Design reproducible drills for multiple Windows AGY sessions.

## Deliverables

- Manual test plan for staggered `p1`, `p2`, and `p3` launches.
- Observations to capture: account header, prompt behavior, refresh behavior.
- Criteria for declaring concurrent use safe, risky, or unsupported.

## Validation Focus

- Drill can be repeated without exposing tokens.
- Outcomes map to explicit product behavior.

## Completion Evidence

- Added `scripts/agy_windows_concurrency_drill.ps1` with a dry-run plan by
  default and `-Run` for staggered local `p1`, `p2`, and `p3` launch drills.
- Criteria are explicit: one Windows user is `unsupported` for true parallel
  AGY isolation; separate Windows users are required for parallel isolation.
- The drill captures diagnostics and recovery commands without printing token
  material.
