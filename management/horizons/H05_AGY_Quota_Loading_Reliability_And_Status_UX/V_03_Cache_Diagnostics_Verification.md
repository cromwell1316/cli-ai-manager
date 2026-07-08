# V_03 Cache Diagnostics Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Required Checks

- Fresh cache entries render immediately and do not queue unnecessary refreshes.
- Stale cache entries render immediately and queue a background refresh.
- Failed refreshes do not erase the last successful quota values.
- Retry backoff prevents immediate repeated probes after failures.
- Diagnostic warnings preserve the real reason for failure.

## Evidence

Pending implementation.
