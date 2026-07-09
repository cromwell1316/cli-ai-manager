# H_03 Phase 03 Launch Wrapper And OS Backends

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Route native process startup through one launch wrapper that applies the selected
resource policy.

## Scope

- Add a small process policy module with backend selection.
- Prefer `systemd-run --user --scope` when available for memory and CPU caps.
- Use Python `resource.setrlimit` for soft fallback limits where supported.
- Use `os.nice` and `ionice` when available for priority reduction.
- Keep terminal attachment behavior correct for interactive launches.
- Ensure child process groups are tracked for cleanup and diagnostics.

## Acceptance

- Launch, login, and add flows use the wrapper.
- Tests verify backend command construction without invoking real systemd.
- Fallback behavior is deterministic when resource controls are unavailable.
