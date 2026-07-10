# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Acceptance Criteria

| Area | Required Result | Evidence |
| --- | --- | --- |
| User discovery | WSL prefers Windows user with managed profile roots over empty Admin | Unit test |
| Explicit user | `USERPROFILE` remains authoritative | Unit test |
| WSL path paste | POSIX import converts `C:\...` to `/mnt/c/...` | Unit test |
| Native Windows path | Windows import keeps `C:\...` unchanged | Unit test |
| Sync compatibility | Existing sync tests still pass | Automated suite |
| Governance | Horizon docs pass governance checks | Full test suite |
