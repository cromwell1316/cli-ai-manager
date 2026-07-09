# V_01 Config Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Resource limit environment variables appear in config metadata.
- Invalid values produce warnings and safe fallbacks.
- Disabling limits is explicit and visible.
- Quota-specific limits override generic process limits where configured.

## Evidence

- `python3 profile_manager.py config show --json` completed successfully and
  showed local backends: launch=`systemd-run`, quota=`setrlimit`,
  validation=`setrlimit`.
- `tests/test_profile_manager.py::test_config_show_json_reports_effective_values_and_invalid_env_warnings`
  covers process limit config metadata, invalid values, and quota overrides.
