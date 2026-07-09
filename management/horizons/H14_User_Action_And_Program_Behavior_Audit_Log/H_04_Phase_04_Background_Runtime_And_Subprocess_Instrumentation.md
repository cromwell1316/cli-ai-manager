# H_04 Phase 04 Background Runtime And Subprocess Instrumentation

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Extend audit coverage to background work, runtime service calls, quota workers,
and native subprocess launch paths.

## Scope

- Audit quota job lifecycle: queued, coalesced, started, completed, failed,
  retried, stale-cache reused, and invalidated.
- Audit persistent PTY session creation, reuse, eviction, recovery, and close
  without storing screen buffers.
- Audit runtime service start, stop, health, request handling, fallback, and
  cache invalidation.
- Audit native CLI subprocess launch attempts and resource policy selection.
- Include elapsed time and sanitized process policy metadata for performance and
  reliability investigations.

## Acceptance

- Background operations keep correlation when triggered by a user action.
- Standalone background operations still have traceable root event IDs.
- No raw PTY output or credential-bearing environment variables are persisted.
- Tests cover quota, runtime service, and subprocess audit events.
