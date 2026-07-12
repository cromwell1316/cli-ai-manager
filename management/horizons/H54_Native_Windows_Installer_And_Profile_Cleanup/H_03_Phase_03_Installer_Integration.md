# H_03 Phase 03 Installer Integration

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Objective

Integrate profile conflict checks into Windows install and verification.

## Work

- Keep Python launcher selection robust.
- Report execution policy and UNC path implications.
- Verify helper freshness without false stale failures.

## Exit Criteria

`verify_install_windows.ps1` reports profile conflicts with repair commands.

