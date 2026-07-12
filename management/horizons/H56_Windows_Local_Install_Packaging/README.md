# H56 Windows Local Install Packaging

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Provide a native Windows install layout that does not depend on WSL UNC paths for
day-to-day use.

## Goals

- Define a Windows-local application source or packaged runtime directory.
- Support update and rollback from the Windows-local install.
- Keep generated shims stable across project moves.
- Verify install behavior without relying on `\\wsl.localhost` paths.
- Document recommended developer and production install modes.

## Non-Goals

- Do not replace WSL/Linux installation.
- Do not require a public package registry before local packaging is proven.
- Do not bundle real credentials or profile data.

## Phases

- Phase 01: install layout and source-copy strategy.
- Phase 02: shim generation against Windows-local paths.
- Phase 03: update, rollback, and uninstall commands.
- Phase 04: documentation and Windows smoke coverage.

## Verification

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man --help
```

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
```

Acceptance target: native Windows `ai-man` continues to work after WSL is
closed, unavailable, or the repo is moved inside WSL.

## Implementation Evidence

- `install-windows.ps1` now copies application files into
  `%LOCALAPPDATA%\Programs\ai-man\app` by default and points shims at that
  Windows-local entrypoint.
- `-DevSource` preserves checkout/UNC shim behavior for active development.
- `-Rollback` restores the latest `app.rollback-YYYYMMDD-HHMMSS` backup, and
  `-Uninstall` removes generated app/shim/helper files without deleting managed
  profiles.
- `scripts/verify_install_windows.ps1` validates the configured `AppDir`,
  distinguishes local installs from development source mode, and fails local
  verification if the app source is UNC.
- `scripts/windows_ci_smoke.ps1` installs into temporary Windows-local app/bin
  paths and checks that shims point at the copied app.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Install_Layout.md`
- `H_02_Phase_02_Source_Copy_And_Shims.md`
- `H_03_Phase_03_Update_And_Rollback.md`
- `H_04_Phase_04_CI_And_Runbook.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
