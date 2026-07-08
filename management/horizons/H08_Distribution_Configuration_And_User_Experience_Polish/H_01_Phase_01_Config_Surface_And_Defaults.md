# H_01 Phase 01 Config Surface And Defaults

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make runtime configuration visible and predictable.

## Scope

- Add `config show --json` or include config in diagnostics.
- Document all supported env vars.
- Validate numeric env vars with clear warnings.
- Keep env vars as the source of override truth.

## Acceptance

- Users can see effective profile roots and quota tuning values.
- Invalid env vars fall back safely and report diagnostics.
