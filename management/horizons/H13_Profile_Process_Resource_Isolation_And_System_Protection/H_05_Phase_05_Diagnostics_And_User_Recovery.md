# H_05 Phase 05 Diagnostics And User Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make resource isolation visible and recoverable when limits are too strict or a
native CLI misbehaves.

## Scope

- Show effective backend and limits in diagnostics.
- Report when systemd/cgroups are unavailable and which fallback is active.
- Add warnings for killed or refused child processes.
- Add user-facing troubleshooting notes for raising memory limits.
- Provide a safe way to close persistent quota sessions and child process groups.

## Acceptance

- Diagnostics explain whether process isolation is active.
- Users can identify a resource-limit failure without reading raw logs.
- Cleanup commands do not touch unrelated processes.
