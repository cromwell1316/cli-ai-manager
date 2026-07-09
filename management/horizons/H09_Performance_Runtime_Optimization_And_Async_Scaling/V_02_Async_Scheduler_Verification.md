# V_02 Async Scheduler Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Duplicate jobs are coalesced by `(tool, profile)`.
- Manual refresh priority is verified with fake workers.
- Worker shutdown does not leak threads when concurrency changes.
- Retry backoff uses fake time and cannot busy-loop.
- Diagnostics expose scheduler counters.

## Evidence

- `InteractiveQuotaScheduler` uses a bounded worker pool with a priority queue,
  per-job sequence numbers, and scheduler counters for submitted, coalesced,
  started, completed, failed, and cancelled jobs.
- `force_quota_refresh` submits manual refresh jobs with priority `0`; automatic
  refresh jobs use priority `10`.
- Duplicate active refresh requests increment the scheduler `coalesced` metric
  instead of enqueueing another `(tool, profile)` job.
- Tests cover non-serialized loads, configured AGY concurrency, duplicate job
  reuse, retry backoff, force-refresh stale preservation, and scheduler metrics.
