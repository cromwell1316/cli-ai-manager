# H_03 Phase 03 PTY Session Lifecycle Hardening

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: implementation phase

Status: completed.

## Objective

Ensure PTY quota sessions start, reuse, recover, and close safely.

## Scope

- Bound session count, idle TTL, startup timeout, command timeout, and cleanup.
- Detect dead subprocesses before reuse.
- Close sessions on profile invalidation and application shutdown.
- Record sanitized session diagnostics.
- Verify resource policy integration for quota subprocesses.

## Acceptance

- Stale sessions are not reused.
- Session eviction is deterministic.
- Cleanup runs after failures and invalidation.
