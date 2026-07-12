# H_01 Phase 01 Profile Conflict Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Identify PowerShell profile constructs that can shadow or break the installed
application.

## Work

- Detect functions named `ai-man`, `profile-man`, `pman`, `agy`, and `codex`.
- Detect dot-sourced files that no longer exist.
- Detect PATH ordering that hides installed shims.

## Exit Criteria

Diagnostics can explain why `Get-Command ai-man` is not resolving to the
installed shim.

## Implementation Notes

- `scripts/repair_windows_profile.ps1` inventories stale functions, aliases,
  missing dot-sourced files, and legacy ai-man/agy/codex profile references.
- `scripts/verify_install_windows.ps1` reports blocking profile conflicts and
  current `Get-Command` resolution for installed shims.
