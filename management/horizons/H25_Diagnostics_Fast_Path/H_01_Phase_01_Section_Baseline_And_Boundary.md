# H_01 Phase 01 Section Baseline And Boundary

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Implementation Notes

- Full audit event scanning was identified as the largest fast-path bottleneck.
- Live process policy systemd checks were excluded from fast mode.
- Deep mode remains available for complete troubleshooting output.

## Objective

Measure each diagnostics section and define which sections belong to fast and
deep modes.

## Deliverables

- Per-section timing baseline.
- Fast/deep section boundary.
- Compatibility notes for existing JSON consumers.
- List of expensive probes that can be cached safely.
