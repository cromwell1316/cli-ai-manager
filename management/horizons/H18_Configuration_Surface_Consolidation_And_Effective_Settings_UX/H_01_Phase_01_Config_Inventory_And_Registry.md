# H_01 Phase 01 Config Inventory And Registry

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Inventory all settings and define their central registry entries.

## Scope

- Inventory environment variables and metadata settings.
- Define setting name, type, default, env alias, validation, redaction, and docs.
- Cover quota, runtime service, process policy, audit, rendering, paths, and
  diagnostics.
- Preserve existing env names as aliases.

## Acceptance

- Every existing config knob has a registry entry or a documented exclusion.
- Type conversion and fallback behavior are consistent.
- Secret-like settings have display redaction.

## Implementation Evidence

- `CONFIG_REGISTRY` covers path, sync, interactive quota, runtime service,
  audit, quota, launch process, quota process, and validation process settings.
- Each registered setting defines type, default, env aliases, category,
  validation bounds, redaction behavior, and description.
- Secret-like quota command overrides are redacted in effective settings and
  diagnostics.
