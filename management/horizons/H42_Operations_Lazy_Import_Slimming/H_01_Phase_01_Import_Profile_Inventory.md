# H_01 Phase 01 Import Profile Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Identify operation imports that materially affect cold startup.

## Deliverables

- Import-time profile for `profile_manager`.
- List of operation dependencies by command path.
- Candidate imports with measured cost and risk.
- Decision list for imports intentionally left unchanged.

## Implementation Notes

- Prefer measurement over broad style cleanup.
- Avoid moving imports that are needed by most commands.
- Track circular import risk before editing.
