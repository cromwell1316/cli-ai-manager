# H_01 Phase 01 Install Layout

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Define the Windows-local application layout and ownership boundaries.

## Work

- Choose application source/runtime directory.
- Separate generated shims from managed profiles.
- Keep user credentials outside package files.

## Exit Criteria

Installer docs specify where application files, shims, helper, and profiles live.

## Implementation Notes

- Default Windows layout is `InstallRoot=%LOCALAPPDATA%\Programs\ai-man`,
  `AppDir=<InstallRoot>\app`, `BinDir=<InstallRoot>\bin`, and
  `AgyHome=%USERPROFILE%\agy-homes`.
- Credentials and profiles remain outside the app package.
