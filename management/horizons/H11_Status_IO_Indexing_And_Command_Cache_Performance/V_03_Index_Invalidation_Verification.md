# V_03 Index Invalidation Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Command-scoped caches expire at command end.
- Profile changes are visible to the next command.
- Import/export/clear/sync flows do not reuse stale command snapshots.

## Evidence

- Caches are fields on `CommandSnapshot`; each CLI command creates a fresh
  snapshot and there is no process-global status or account cache.
- Direct import/export/clear/sync helpers still call direct filesystem helpers
  and do not retain command snapshots.
