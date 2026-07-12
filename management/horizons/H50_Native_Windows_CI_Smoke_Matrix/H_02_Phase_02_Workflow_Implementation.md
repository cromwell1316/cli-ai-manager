# H_02 Phase 02 Workflow Implementation

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Implement the native Windows CI workflow.

## Deliverables

- Windows job for syntax checks.
- Focused `windows` pytest selection.
- Installer smoke with custom `BinDir` and `AgyHome`.
- Helper generation assertion.

## Validation Focus

- CI fails on installer and helper regressions.
- CI remains fast and token-safe.
