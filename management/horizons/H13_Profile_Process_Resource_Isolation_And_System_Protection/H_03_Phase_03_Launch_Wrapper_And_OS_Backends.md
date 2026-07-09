# H_03 Phase 03 Launch Wrapper And OS Backends

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

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

## Evidence

- `cli_profile_manager/process_policy.py` selects `systemd-run`, `setrlimit`,
  `priority-only`, `disabled`, or `unsupported` backends deterministically.
- `tests/test_profile_manager.py::test_process_policy_builds_systemd_scope_command`
  covers systemd command construction without requiring live systemd in CI.
- `tests/test_profile_manager.py::test_run_cli_tool_uses_process_policy_wrapper`
  verifies launch/login/add native CLI paths route through the wrapper.
