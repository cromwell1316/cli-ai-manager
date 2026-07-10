# H_02 Phase 02 Fast Collector And Cached Probes

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Implementation Notes

- Fast collector returns lightweight process policy and audit summaries.
- Deep collector retains full audit, interactive quota runtime, and process
  policy diagnostics.
- CLI exposes the boundary through `--deep`.

## Objective

Implement section-level collectors and route common diagnostics through the
fast collector.

## Deliverables

- Fast diagnostics collector.
- Deep diagnostics collector.
- Cached process/service checks.
- Tests for redaction and output shape.
