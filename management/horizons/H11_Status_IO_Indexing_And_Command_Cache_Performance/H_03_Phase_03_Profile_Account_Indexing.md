# H_03 Phase 03 Profile Account Indexing

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Reduce repeated account lookup work where the source data is stable within a
command execution.

## Scope

- Cache AGY account lookup results inside the command snapshot.
- Avoid repeated log scans for the same `(tool, profile)` during diagnostics.
- Invalidate command snapshots naturally at process/command end.
- Keep persistent account indexing out unless a later phase proves it safe.

## Acceptance

- Diagnostics and status reuse account lookup results inside one command.
- No credential token values are cached or logged.

## Evidence

- `tests/test_profile_manager.py::test_command_snapshot_reuses_agy_account_lookup`
  verifies AGY account lookup is cached per profile inside the command snapshot.
- The snapshot stores derived account identifiers only, not raw OAuth or CLI
  token payloads.
