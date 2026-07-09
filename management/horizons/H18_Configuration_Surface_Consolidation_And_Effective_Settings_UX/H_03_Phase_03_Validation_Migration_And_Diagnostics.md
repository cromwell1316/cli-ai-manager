# H_03 Phase 03 Validation Migration And Diagnostics

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Move scattered parsing and fallback logic onto the registry and surface
configuration problems through diagnostics.

## Scope

- Replace local env parsing helpers with registry-backed accessors.
- Emit warnings for invalid values and unsafe combinations.
- Include config health in diagnostics.
- Ensure runtime service and one-shot commands resolve config consistently.

## Acceptance

- Invalid config is reported clearly.
- One-shot and service-backed paths agree on effective settings.
- Diagnostics include redacted config health.

## Implementation Evidence

- Registry parsing reports invalid bool, integer, float, enum, and bounded
  values through warnings.
- Diagnostics include `config_health` and `effective_config` from the registry.
- Legacy `profile_roots`, `quota`, `process_limits`, and `warnings` fields stay
  available for one-shot and service-backed read-only command paths.
