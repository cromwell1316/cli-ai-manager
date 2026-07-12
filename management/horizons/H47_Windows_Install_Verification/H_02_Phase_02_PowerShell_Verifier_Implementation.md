# H_02 Phase 02 PowerShell Verifier Implementation

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

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
