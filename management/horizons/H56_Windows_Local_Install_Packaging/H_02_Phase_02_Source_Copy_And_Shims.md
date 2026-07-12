# H_02 Phase 02 Source Copy And Shims

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Install or copy application source to a Windows-local path and generate stable
shims.

## Work

- Copy required Python package files and entrypoint.
- Generate shims against the installed Windows path.
- Verify direct commands and no-args interactive startup.

## Exit Criteria

`Get-Command ai-man` resolves to a shim that points at Windows-local files.

## Implementation Notes

- Installer copies `profile_manager.py`, `cli_profile_manager`, docs, and
  Windows support scripts into the configured app directory.
- Generated PowerShell and CMD shims point at the installed app entrypoint unless
  `-DevSource` is explicitly selected.
