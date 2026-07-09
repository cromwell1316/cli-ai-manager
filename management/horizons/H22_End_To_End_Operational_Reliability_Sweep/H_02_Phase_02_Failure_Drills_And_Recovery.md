# H_02 Phase 02 Failure Drills And Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Exercise failure paths and recovery guidance end to end.

## Scope

- Simulate missing CLIs, invalid credentials, denied permissions, broken JSON,
  stale runtime sockets, quota timeouts, sync conflicts, and audit backend
  failures.
- Verify recovery messages, diagnostics, audit records, and exit codes.
- Verify no partial mutation is hidden from the user.

## Acceptance

- Failure drills have deterministic expected results.
- Recovery guidance is actionable.
- Audit and diagnostics agree on failure facts.
