# H_04 Phase 04 Quota PTY Resource Bounds

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Apply stricter resource policies to background quota probes and persistent PTY
sessions.

## Scope

- Apply quota-specific memory, CPU, process count, nice, and IO priority limits.
- Ensure persistent quota sessions inherit limits when created.
- Enforce max session count and idle TTL together with process limits.
- Handle failures from limit application as explicit diagnostics rather than
  silent hangs.
- Keep stale quota values visible if a limited quota process fails.

## Acceptance

- Quota PTY process startup uses the resource policy wrapper.
- Resource-limit failures produce safe `quota` states and warnings.
- Existing stale quota preservation and retry behavior remain intact.

## Evidence

- `tests/test_profile_manager.py::test_quota_pty_uses_quota_process_policy`
  verifies one-shot PTY quota subprocesses receive the quota policy.
- Persistent quota sessions share the same `PersistentQuotaSession.start()`
  policy hook.
- `resource_limited` failures invalidate persistent sessions and preserve stale
  quota values in interactive status refresh.
