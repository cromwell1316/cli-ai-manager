# H_02 Phase 02 PowerShell Verifier Implementation

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Implement the native Windows verification script.

## Deliverables

- `scripts/verify_install_windows.ps1`.
- Structured success and failure output.
- Optional custom `BinDir` and `AgyHome` support.
- Safe helper freshness check.

## Validation Focus

- Fresh installs pass verification.
- Missing shim, missing Python, and missing helper cases fail clearly.

## Result

`scripts/verify_install_windows.ps1` was implemented with structured `[OK]`,
`[WARN]`, and `[FAIL]` output. It verifies shim files in the configured bin
directory, confirms they point at `profile_manager.py`, checks helper freshness
against `windows_agy_helper_source`, and performs a reversible Credential
Manager read/write/delete check using a temporary target.
