# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: horizon brief

Status: implemented.

## Problem

The application now has reliable profile, quota, diagnostics, and live
validation behavior, but the runtime has grown around synchronous filesystem
reads, PTY waits, background threads, and large mixed-responsibility modules.
Recent fixes improved the AGY status screen by avoiding repeated profile I/O
during quota polling, but that is only one local optimization. The next step is
a measured performance program that treats responsiveness and runtime cost as
first-class product constraints.

## Current Audit Findings

- `cli_profile_manager/interactive.py` is roughly 1350 lines and owns UI
  rendering, key handling, quota cache state, scheduler state, profile actions,
  sync entrypoints, and status collection.
- `cli_profile_manager/cli.py` is roughly 1200 lines and still acts as a broad
  compatibility and command surface layer.
- `cli_profile_manager/quota.py` combines terminal parsing, PTY lifecycle,
  process IO, persistent sessions, parser miss accounting, and payload shaping.
- AGY quota probes are dominated by fixed startup/post-command waits and PTY
  idle detection. This is reliable but expensive when probing many profiles.
- Status and diagnostics paths repeatedly walk profile roots, metadata, and
  account files. AGY account fallback may scan recent local logs.
- Async quota scheduling is bounded by worker count, but it has no explicit
  priority model, queue coalescing contract, cancellation policy, or metrics
  budget.
- UI redraws are improved but still recompute render strings and quota
  summaries frequently while probes are active.
- Test coverage is broad for behavior, but there are no performance budgets,
  fake-clock benchmark fixtures, or regression tests around maximum filesystem
  calls, redraw cost, queue coalescing, or PTY wait behavior.

## Desired End State

The tool should have measured baselines, explicit performance budgets, and an
optimized runtime architecture. Interactive status screens should render
quickly, preserve useful stale data, and schedule refresh work without duplicate
jobs or unnecessary filesystem reads. PTY sessions should be reused and
invalidated predictably. Performance regressions should fail tests before they
reach users.
