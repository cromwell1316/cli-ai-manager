# H_01 Phase 01 Config Payload Profile

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Measure where `config show --json` spends time before changing construction
logic.

## Deliverables

- Profile of `effective_config_payload`.
- List of repeated conversions or merges.
- JSON schema snapshot for regression comparison.
- Decision on health payload boundaries.

## Implementation Notes

- Treat schema stability as the primary constraint.
- Separate plain config output from health probes.
- Avoid micro-optimizations without measurable impact.

## Profile Findings

- `effective_config_payload(include_sources=True)` itself is sub-millisecond;
  JSON serialization and command dispatch dominate warm command time.
- Cold `config show --json` still paid for import-time work from `dataclasses`,
  `pathlib`, and live `process_policy` even though plain config output only
  needs deferred process policy data.
- Repeated construction existed in the settings path:
  - build all settings
  - derive public settings
  - build `settings_by_key`
  - collect warnings

## Decisions

- Optimize construction and import surface only where schema-equivalent.
- Keep live `process_policy` import for `config health`.
- Keep JSON serialization unchanged because output formatting is part of the
  command surface.
