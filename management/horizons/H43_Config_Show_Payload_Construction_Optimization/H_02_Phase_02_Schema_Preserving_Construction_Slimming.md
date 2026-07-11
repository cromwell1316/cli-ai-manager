# H_02 Phase 02 Schema Preserving Construction Slimming

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

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
