# H_03 Phase 03 Policy Warnings And Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Add user-facing policy, warnings, and recovery commands.

## Deliverables

- Warning text for risky concurrent AGY launches.
- Recovery flow for restoring a selected backup to the live slot.
- Documentation for separate Windows users when true isolation is required.

## Validation Focus

- Warnings are shown only where relevant.
- Recovery path is auditable and token-safe.

## Completion Evidence

- Native Windows AGY launch/login emits a shared-slot warning before invoking
  the managed helper.
- The managed helper serializes `launch`, `login`, `set`, `save`, and `clear`
  with `Global\ai-man-agy-credential-slot`.
- Recovery is documented as closing active AGY sessions, restoring a selected
  profile with `ai-man launch agy pN`, refreshing with `ai-man login agy pN`,
  and checking `ai-man diagnostics agy --json --show-accounts`.
