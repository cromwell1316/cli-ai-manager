# H13 Profile Process Resource Isolation And System Protection

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Prevent launched profile CLIs and quota probe subprocesses from consuming enough
memory, CPU, process slots, or IO priority to slow down the main system.

## Goals

- Add configurable per-profile resource limits for launched native agent
  processes.
- Apply safe default limits to quota probe subprocesses and persistent PTY
  sessions.
- Prefer OS-native isolation where available: `systemd-run --user` scopes,
  cgroups, `resource.setrlimit`, `nice`, and `ionice`.
- Provide deterministic fallback behavior for Linux/WSL environments where
  systemd user scopes are unavailable.
- Expose effective limits in `config show`, diagnostics, and debug logs without
  leaking credentials.
- Add tests proving resource limit configuration is passed to process launch
  paths.

## Non-Goals

- Do not sandbox credentials away from the native CLI in this horizon.
- Do not add container runtimes as a required dependency.
- Do not silently kill active user sessions without clear status/diagnostics.
- Do not apply aggressive defaults that break normal CLI startup.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Process_Inventory_And_Risk_Model.md`
- `H_02_Phase_02_Resource_Limit_Config_Surface.md`
- `H_03_Phase_03_Launch_Wrapper_And_OS_Backends.md`
- `H_04_Phase_04_Quota_PTY_Resource_Bounds.md`
- `H_05_Phase_05_Diagnostics_And_User_Recovery.md`
- `H_06_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Config_Verification.md`
- `V_02_Launch_Backend_Verification.md`
- `V_03_Quota_Bounds_Verification.md`
- `V_04_Acceptance_Matrix.md`
