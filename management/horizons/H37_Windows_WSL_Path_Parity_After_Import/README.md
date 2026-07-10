# H37 Windows WSL Path Parity After Import

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Fix Windows/WSL profile path selection after WSL import and sync. The manager
must not write converted credentials into the wrong Windows user directory, and
native Windows paths must not be rewritten to WSL `/mnt/c` paths.

## Goals

- Prefer the Windows user directory that actually contains managed profile
  roots when running from WSL.
- Preserve explicit `AI_MAN_WINDOWS_HOME` and native `USERPROFILE` overrides.
- Convert `C:\...` paths to `/mnt/c/...` only outside native Windows.
- Keep AGY credential conversion model unchanged.
- Add deterministic tests for Admin-vs-Oliver user selection and path
  normalization.

## Non-Goals

- Do not migrate or delete existing profile directories.
- Do not edit Windows Credential Manager entries.
- Do not rewrite the legacy Windows prototype outside this repository.
- Do not change Codex, Claude, or AGY credential file formats.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Windows_User_Discovery.md`
- `H_02_Phase_02_Platform_Path_Normalization.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
