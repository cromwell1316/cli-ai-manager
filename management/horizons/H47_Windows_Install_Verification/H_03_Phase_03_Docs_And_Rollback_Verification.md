# H_03 Phase 03 Docs And Rollback Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document Windows verification and rollback.

## Deliverables

- README instructions for install verification.
- Rollback steps for shims and PATH changes.
- Troubleshooting notes for execution policy and stale shell PATH.

## Validation Focus

- A user can install, verify, and rollback from documented commands.
- Verification output does not expose secrets.

## Result

README now includes native Windows verification commands, custom verifier
arguments, troubleshooting for execution policy and stale shell PATH, and manual
rollback commands for generated Windows shims and the managed AGY helper.
