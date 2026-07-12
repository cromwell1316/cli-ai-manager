# H_02 Phase 02 Helper Integrated Quota Execution

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Implement the Windows quota runner through the managed AGY helper.

## Deliverables

- Native Windows runner that applies `cred-pN.json` before probing.
- Timeout and process failure handling.
- Redacted audit events for quota subprocess attempts.
- Unit coverage for helper argv generation.

## Validation Focus

- Selected profile credential is applied before AGY runs.
- Missing backup returns a clear no-token/auth-required state.
- Runtime failures are surfaced without leaking token data.
