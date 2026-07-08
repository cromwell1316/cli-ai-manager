# V_03 Cache Diagnostics Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Required Checks

- Fresh cache entries render immediately and do not queue unnecessary refreshes.
- Stale cache entries render immediately and queue a background refresh.
- Failed refreshes do not erase the last successful quota values.
- Retry backoff prevents immediate repeated probes after failures.
- Diagnostic warnings preserve the real reason for failure.

## Evidence

- `pytest -q` passes with cache coverage for fresh reuse, stale value display
  during refresh, failed refresh preservation, retry backoff, and diagnostics.
- `python -m compileall cli_profile_manager profile_manager.py` passes.
