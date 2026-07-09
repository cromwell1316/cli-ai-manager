# H_02 Phase 02 Resource Limit Config Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Expose resource limits as explicit, documented configuration.

## Scope

- Add environment variables for defaults such as:
  - `AI_MAN_PROCESS_LIMITS`
  - `AI_MAN_PROCESS_MEMORY_MB`
  - `AI_MAN_PROCESS_CPU_PERCENT`
  - `AI_MAN_PROCESS_MAX_PROCESSES`
  - `AI_MAN_PROCESS_NICE`
  - `AI_MAN_PROCESS_IONICE_CLASS`
  - `AI_MAN_QUOTA_PROCESS_MEMORY_MB`
  - `AI_MAN_QUOTA_PROCESS_CPU_PERCENT`
- Support disabling limits explicitly for debugging.
- Validate numeric ranges and report warnings for invalid values.
- Include effective policy in `config show --json`.
- Include active backend and policy in diagnostics.

## Acceptance

- Invalid limit values fall back safely with warnings.
- Defaults are conservative and do not break normal CLI startup.
- Config output shows exactly what policy will be applied.

## Evidence

- `config show --json` includes `process_limits.launch`,
  `process_limits.quota`, and `process_limits.validation`.
- `tests/test_profile_manager.py::test_config_show_json_reports_effective_values_and_invalid_env_warnings`
  verifies invalid process limit values produce warnings and safe fallbacks.
