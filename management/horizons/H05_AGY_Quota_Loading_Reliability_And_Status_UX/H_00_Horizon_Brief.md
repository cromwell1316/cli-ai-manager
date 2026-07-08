# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Problem

AGY quota probing is implemented by driving the real `agy` CLI through a PTY and
typing `/usage`. A single profile can work, but starting every profile at once is
not operationally reliable. It creates many expensive interactive processes,
competes for network and local resources, and makes the UI show only `load` or
`retry` without explaining what happened.

The manager needs a quota subsystem that behaves like a background service:
fast status first, controlled refresh work second, cached data reused whenever
possible, and visible failure reasons when AGY cannot return data.

## Strategy

Create an explicit quota scheduler for interactive status views. The scheduler
owns bounded worker concurrency, per-profile persistent PTY sessions, cache
freshness, stale display, refresh state, and diagnostics. The status renderer
should only read snapshots from this subsystem and never directly manage thread
or process lifecycle.

## Success Criteria

- Opening AGY status renders profile/account/token rows immediately.
- At most the configured number of AGY quota probes run at the same time.
- Fresh cached quota values render immediately on repeated status views.
- Stale cached values still render while a refresh is queued or running.
- A persistent AGY PTY session is reused for repeated quota probes in the same
  manager process.
- Failed quota probes show a compact diagnostic marker and preserve detailed
  warnings in cache/JSON-compatible data.
- AGY quota columns remain stable and readable: `FM`, `FH`, `FL`, `PL`, `PH`,
  `CS`, `CO`, plus any discovered extra pools.
- Tests cover the scheduler and renderer without needing real AGY credentials.
