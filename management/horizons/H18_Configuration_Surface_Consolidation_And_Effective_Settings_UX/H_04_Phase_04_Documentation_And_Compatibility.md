# H_04 Phase 04 Documentation And Compatibility

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Keep existing users working while making configuration easier to discover.

## Scope

- Document all settings, defaults, aliases, and examples.
- Add compatibility aliases for legacy environment variables.
- Add deprecation warnings only where migration is necessary.
- Update README and diagnostics examples.

## Acceptance

- Existing documented env vars keep working.
- New docs reflect registry defaults.
- Deprecated settings have clear replacement guidance.

## Implementation Evidence

- Existing `AI_MAN_*` environment variable names remain the primary aliases.
- `CONFIG_ENV_VARS` is generated from the central registry for documentation
  and display compatibility.
- No global system config file is required.
