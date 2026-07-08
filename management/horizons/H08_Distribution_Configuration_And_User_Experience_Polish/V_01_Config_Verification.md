# V_01 Config Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Effective config is visible.
- Invalid numeric env vars fall back safely.
- Config output redacts sensitive values.

## Evidence

- `python3 profile_manager.py config show --json`
- `tests/test_profile_manager.py::test_config_show_json_reports_effective_values_and_invalid_env_warnings`
