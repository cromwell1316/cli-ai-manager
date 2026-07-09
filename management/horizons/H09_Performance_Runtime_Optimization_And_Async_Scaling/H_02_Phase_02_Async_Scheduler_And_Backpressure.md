# H_02 Phase 02 Async Scheduler And Backpressure

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make background quota work explicit, deduplicated, bounded, and observable.

## Scope

- Replace implicit queue semantics with a small scheduler contract:
  `queued`, `running`, `ready`, `retryable`, `cancelled`, and `closed`.
- Coalesce duplicate jobs for the same `(tool, profile)`.
- Support priority for manual refresh over passive auto-refresh.
- Keep stale quota values visible while refresh jobs run.
- Add queue metrics: submitted, coalesced, started, completed, failed,
  cancelled, active worker count, queue depth, and average job age.
- Add safe shutdown semantics for worker replacement when concurrency changes.
- Prevent tight retry loops with fake-clock tests.

## Acceptance

- Manual refresh never creates duplicate jobs for profiles already queued or
  running.
- Auto refresh does not starve manual refresh.
- Changing AGY concurrency does not leak old worker threads.
- Diagnostics expose scheduler counters without credentials.
