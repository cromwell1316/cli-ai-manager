# V_02 Command Surface Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- `config show` displays effective values.
- `--sources` displays source information.
- JSON output is stable.
- Diagnostics include config health.
- Legacy environment variables continue working.

## Verification Evidence

`config show --json --sources --filter session_max` is covered by tests and
reports the effective value, source type, and source environment name.
Diagnostics expose `config_health` and redacted `effective_config`.
