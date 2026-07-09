# V_03 Quota Bounds Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Quota PTY sessions receive quota-specific resource policies.
- Persistent sessions remain bounded by TTL, max count, and process limits.
- Resource-limit failures preserve stale quota values and report warnings.
- Scheduler concurrency still bounds the number of simultaneous probes.

## Evidence

- `tests/test_profile_manager.py::test_quota_pty_uses_quota_process_policy`
  verifies quota PTY startup passes through the quota process policy.
- Existing scheduler/session tests continue to pass with policy wrapping.
- `tests/test_profile_manager.py::test_interactive_stale_quota_survives_failed_refresh`
  covers stale quota preservation for `resource_limited` failures.
- `python3 profile_manager.py quota agy p1 --json --timeout 5` was exercised
  manually on the local host; when a native CLI exceeds the configured quota
  memory budget, the result remains a structured quota state with warnings.
