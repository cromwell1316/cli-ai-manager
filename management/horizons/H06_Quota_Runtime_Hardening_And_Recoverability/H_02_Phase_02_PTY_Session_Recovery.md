# H_02 Phase 02 PTY Session Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Prevent corrupted or timed-out PTY sessions from being reused for later quota
requests.

## Scope

- Treat timeout and process-exit class failures as session-invalidating.
- Close and remove the persistent session when a quota snapshot fails with an
  invalidating state.
- Track repeated parser misses per session and invalidate after a small
  threshold.
- Preserve profile isolation: never share a session between profile homes.

## Acceptance

- A timeout closes the matching persistent session.
- The next quota request for the same profile creates a fresh session.
- Sessions for other profiles remain alive.
- Tests cover dead-session replacement and timeout-session invalidation.
