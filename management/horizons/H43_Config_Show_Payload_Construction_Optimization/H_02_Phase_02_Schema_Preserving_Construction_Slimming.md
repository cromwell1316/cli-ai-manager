# H_02 Phase 02 Schema Preserving Construction Slimming

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Slim config payload construction without changing output fields or values.

## Deliverables

- Targeted construction simplifications.
- Payload shape regression tests.
- In-process and cold subprocess benchmark evidence.
- Notes for any construction costs intentionally left unchanged.

## Implementation Notes

- Preserve key names, nesting, and value semantics.
- Keep health checks opt-in for health and deep diagnostics paths.
- Avoid broad config model refactors.

## Implementation

- `SettingDefinition` is now a small slots-based class instead of a dataclass.
- Plain `config show` process-limit payloads use a fast local builder that
  matches `process_policy(..., resolve_backend=False)` sampled behavior and
  keeps backend as `deferred`.
- `config health` still imports `process_policy` and resolves live backends.
- `effective_config_payload` now resolves settings, warnings, and key maps in a
  single pass.
- `sync_roots` string construction no longer imports `pathlib` for already
  parsed path values.

## Tests

- Added schema regression for payload key order, setting field order,
  `settings_by_key`, and `include_sources=False` stripping behavior.
- Added subprocess import-boundary regression proving `config show --json`
  does not import `cli_profile_manager.process_policy`.
