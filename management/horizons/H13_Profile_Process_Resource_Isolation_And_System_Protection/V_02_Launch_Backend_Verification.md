# V_02 Launch Backend Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Checks

- Backend selection is deterministic.
- `systemd-run --user --scope` command construction is tested without requiring
  systemd in CI.
- `resource.setrlimit` fallback is unit-tested where supported.
- Interactive launch remains attached to the terminal.

## Evidence

Pending implementation.
