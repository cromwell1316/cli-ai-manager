# H_03 Phase 03 Sync Safety And JSON

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Scope

Make sync auditable and scriptable before it performs writes.

## Requirements

- Support `sync --dry-run --json`.
- For hard sync, report the explicit destination paths that would be deleted.
- Refuse hard sync mutation unless `--yes` is present.
- Refuse deletion outside the resolved destination home.
- Report `copied`, `skipped`, `converted`, `invalid`, and `would_delete`.

## Acceptance

Dry-run must not write converted agy credentials or remove destination files.
Hard sync mutation must be impossible without explicit confirmation.
