# H_01 Phase 01 Verification Surface Design

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Define the Windows verification command contract.

## Deliverables

- Script name, arguments, and exit-code contract.
- Checks for bin directory, shims, PATH, Python, PowerShell, and helper path.
- Token-safe Credential Manager check design.

## Validation Focus

- Verification can run without real AGY credentials.
- Failures are actionable and non-destructive.

## Result

The verifier contract is `scripts/verify_install_windows.ps1` with optional
`-BinDir`, `-AgyHome`, `-SkipPathCheck`, and `-SkipCredentialCheck` arguments.
It returns exit code 0 on success and 1 when install checks fail. PATH staleness
in the current shell is reported as a warning when the user PATH is already
configured.
