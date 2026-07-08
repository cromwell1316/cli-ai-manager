# H_02 Phase 02 Install Update Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make install and update behavior verifiable.

## Scope

- Audit `install.sh` for idempotency.
- Add an install verification script or command.
- Ensure command aliases point at the intended checkout.
- Document rollback/manual cleanup steps.

## Acceptance

- Running install twice is safe.
- Verification confirms `ai-man` and `profile_manager.py` resolve correctly.
