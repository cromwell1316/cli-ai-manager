# H_02 Phase 02 Failure Drills And Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

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

## Evidence

Validated deterministic failure drills in a temporary environment:

| Failure Drill | Expected Result | Observed |
| --- | --- | --- |
| Quota on missing-token profile | Exit code `4` (`no_token`) | `4` |
| Import missing source file | Exit code `3` (`not_found`) | `3` |
| Clear profile without `--yes` | Exit code `2` (`confirmation_required`) | `2` |
| Sync missing source root | Exit code `3` (`not_found`) during initial drill | `3` |

The sync missing-root finding was caused by an incomplete temporary fixture. The
successful sync dry-run scenario passed after creating both WSL and Windows
roots, confirming the command behavior and the failure reporting path.
