# V_01 Diagnostics Command Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Diagnostics command exits successfully without tokens.
- JSON contains profile roots, CLI availability, quota cache, and session counts.
- Output redacts token-like values.

## Evidence

- `python3 profile_manager.py diagnostics agy --json`
- `tests/test_profile_manager.py::test_diagnostics_json_redacts_accounts_and_reports_runtime`
- `tests/test_profile_manager.py::test_diagnostics_command_json_does_not_print_token_like_values`
