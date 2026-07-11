# H_01 Phase 01 Config Payload Profile

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

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
