# H_01 Phase 01 CI Scope And Secrets Boundary

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Define Windows CI scope without using real credentials.

## Deliverables

- CI scenario list.
- Explicit no-token/no-account boundary.
- Temporary path strategy for installer smoke.

## Validation Focus

- Tests do not require AGY login.
- Generated artifacts remain in temporary directories.
