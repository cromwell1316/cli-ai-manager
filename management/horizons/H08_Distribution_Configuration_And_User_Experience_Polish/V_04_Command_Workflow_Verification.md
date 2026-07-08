# V_04 Command Workflow Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Error messages remain actionable.
- JSON contracts stay stable.
- Exit codes remain compatible.

## Evidence

- `tests/test_profile_manager.py::test_direct_command_exit_codes_and_json_errors`
- `tests/test_profile_manager.py::test_config_show_json_reports_effective_values_and_invalid_env_warnings`
