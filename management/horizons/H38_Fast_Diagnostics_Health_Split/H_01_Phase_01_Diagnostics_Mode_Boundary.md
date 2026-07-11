# H_01 Phase 01 Diagnostics Mode Boundary

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Define the exact payload boundary between fast diagnostics and deep diagnostics.

## Deliverables

- Inventory of diagnostics payload fields.
- Identification of live health checks in fast mode.
- Decision record for which fields remain static in fast mode.
- Compatibility notes for existing JSON consumers.

## Implementation Notes

- Keep field names stable where possible.
- Treat process backend probing as a deep diagnostics concern.
- Do not change user-visible command names or flags.

## Result

The diagnostics payload still exposes `config_health` and `effective_config` in
both modes. Fast mode sources them from non-live effective config data; deep
mode sources them from the live health payload.
