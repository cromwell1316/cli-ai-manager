# H_04 Phase 04 Diagnostics Status Reuse

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make diagnostics reuse the same status data shape as command status/list paths
instead of repeating similar discovery work.

## Scope

- Route diagnostics status collection through the command snapshot.
- Preserve diagnostics-specific details such as CLI availability and persistent
  session state.
- Keep account redaction behavior unchanged.
- Add tests for diagnostics output stability.

## Acceptance

- Diagnostics uses measured status snapshots.
- JSON output remains backward compatible.

## Evidence

- `cmd_diagnostics()` now builds one `CommandSnapshot` and passes snapshot-backed
  status and profile indexes into `diagnostics_payload()`.
- `tests/test_profile_manager.py::test_diagnostics_reuses_supplied_profile_indexes`
  verifies diagnostics does not rescan profile roots when indexes are supplied.
