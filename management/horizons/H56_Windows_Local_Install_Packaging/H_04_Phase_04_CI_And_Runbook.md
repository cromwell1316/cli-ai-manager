# H_04 Phase 04 CI And Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Add smoke coverage and documentation for Windows-local packaging.

## Work

- Extend Windows smoke scripts for local package paths.
- Document development UNC mode vs local install mode.
- Add troubleshooting for moved or missing installed files.

## Exit Criteria

CI and docs cover both developer and day-to-day Windows install paths.

## Implementation Notes

- Windows smoke now installs to temporary app/bin paths and verifies local shim
  targets.
- README and runbook document default Windows-local installs, `-DevSource`,
  rollback, uninstall, and moved-checkout recovery.
