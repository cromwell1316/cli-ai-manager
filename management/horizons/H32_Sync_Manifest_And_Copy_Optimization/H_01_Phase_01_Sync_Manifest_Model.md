# H_01 Phase 01 Sync Manifest Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Represent sync input as a manifest with enough facts for diffing.

## Deliverables

- Manifest entry schema.
- Known profile file collectors.
- Destination managed-file collector.
- Dry-run evidence format.

## Result

Sync planning now uses explicit manifests for source and destination roots.
Managed profile roots collect only known profile/config files and record path,
size, mtime, and entry type facts for diffing.
