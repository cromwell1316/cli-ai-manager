# H_01 Phase 01 State Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Model the Windows AGY states that matter to launch, login, recovery, and
diagnostics.

## Work

- Represent managed backup presence and validity.
- Represent live Credential Manager slot availability.
- Represent lock contention and unsupported parallel assumptions.

## Exit Criteria

Diagnostics can classify Windows AGY readiness without printing token material.

## Implementation Notes

- `windows_agy_session_state()` classifies managed backup readiness, live-slot
  policy, action readiness, blockers, and recovery commands without exposing
  credential blobs.
- Diagnostics include `agy_windows_session_guardrails` with token-safe state for
  visible AGY profiles.
