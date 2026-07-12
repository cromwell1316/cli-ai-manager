# H_02 Phase 02 Workflow Implementation

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

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

## Completion Evidence

- Added `.github/workflows/windows-smoke.yml` using `windows-latest` and Python
  3.11.
- Added `scripts/windows_ci_smoke.ps1` to run syntax checks, focused Windows
  pytest, temporary installer smoke, install verification, helper contract
  checks, and horizon governance.
- Added a static regression test that verifies the workflow and smoke script keep
  the token-safe flags and focused Windows test selection.
