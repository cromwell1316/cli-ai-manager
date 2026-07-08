# V_01 Worker Queue Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Required Checks

- Scheduling many AGY profiles respects the configured concurrency limit.
- Duplicate scheduling for the same profile is deduplicated.
- Status rendering can request quota refreshes without waiting for worker
  completion.
- Worker completion updates the cache entry exactly once per finished job.

## Evidence

Pending implementation.
