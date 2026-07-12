# H56 Windows Local Install Packaging

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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

Acceptance target: native Windows `ai-man` continues to work after WSL is
closed, unavailable, or the repo is moved inside WSL.

## Files

- `README.md`

