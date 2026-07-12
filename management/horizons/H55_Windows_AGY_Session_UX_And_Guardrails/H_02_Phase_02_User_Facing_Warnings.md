# H_02 Phase 02 User Facing Warnings

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Make shared-slot behavior visible before risky Windows AGY actions.

## Work

- Add concise launch/login warnings.
- Explain same-user serialization and separate-user isolation.
- Avoid blocking normal flows with excessive prompts.

## Exit Criteria

Users see the Windows AGY limitation at the point where it affects their action.

## Implementation Notes

- Direct CLI and Windows interactive launch/login print shared-slot warnings at
  the point of action.
- Launch explains which managed backup will be restored; login explains that a
  fresh backup will be saved after AGY exits.
