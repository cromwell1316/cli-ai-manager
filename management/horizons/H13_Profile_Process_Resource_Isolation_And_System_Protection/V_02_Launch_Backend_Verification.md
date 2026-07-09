# V_02 Launch Backend Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Backend selection is deterministic.
- `systemd-run --user --scope` command construction is tested without requiring
  systemd in CI.
- `resource.setrlimit` fallback is unit-tested where supported.
- Interactive launch remains attached to the terminal.

## Evidence

- `tests/test_profile_manager.py::test_process_policy_builds_systemd_scope_command`
  verifies `systemd-run --user --scope` construction.
- `tests/test_profile_manager.py::test_process_policy_fallback_prepares_preexec`
  verifies deterministic fallback policy preparation without systemd.
- `tests/test_profile_manager.py::test_run_cli_tool_uses_process_policy_wrapper`
  verifies foreground launch uses the wrapper.
