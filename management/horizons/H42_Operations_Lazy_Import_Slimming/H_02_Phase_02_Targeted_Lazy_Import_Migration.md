# H_02 Phase 02 Targeted Lazy Import Migration

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Move selected heavy imports behind command-specific execution paths.

## Deliverables

- Lazy imports for measured candidates.
- Smoke tests for affected commands.
- Import benchmark comparison.
- Notes for any imports deferred because of risk.

## Implementation Notes

- Keep public modules importable.
- Do not change result classes or payload schemas.
- Keep lazy imports close to the code that uses them.
