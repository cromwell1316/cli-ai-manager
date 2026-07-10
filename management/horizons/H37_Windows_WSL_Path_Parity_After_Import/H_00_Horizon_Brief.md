# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

After WSL import, credentials can be written to the wrong Windows profile root
when `/mnt/c/Users` contains multiple real user directories. The previous
heuristic selected the first non-system directory, which can be `Admin` even
when managed profiles live under `Oliver`.

The legacy Windows prototype also contains WSL-only path rewrites. The supported
manager needs a platform boundary so native Windows paths remain native while
WSL invocations can still accept copied `C:\...` paths.

## Success Criteria

- WSL sync picks the Windows user with existing managed profile roots.
- `USERPROFILE` remains authoritative when explicitly present.
- Native Windows import paths like `C:\Users\Oliver\...` are preserved.
- WSL import paths copied from Windows are normalized to `/mnt/c/...`.
- Existing sync and import behavior remains compatible.
