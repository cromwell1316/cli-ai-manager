# H11 Status IO Indexing And Command Cache Performance

Owner: cli-profile-manager
Source of Truth: management/horizons/H11_Status_IO_Indexing_And_Command_Cache_Performance/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Reduce filesystem work in `list`, `status`, and `diagnostics` by introducing
explicit per-command snapshots and safe indexes for profile metadata that is
expensive to rediscover repeatedly.

## Goals

- Measure filesystem calls per command with fake profile roots.
- Build a command-scoped status snapshot that is reused across table rendering,
  JSON output, diagnostics summaries, and validation paths.
- Add optional profile/account indexes only where invalidation is clear.
- Avoid repeated AGY account log scans in one command execution.
- Preserve correctness when profile files change between commands.

## Non-Goals

- Do not cache credential contents.
- Do not introduce a persistent database in this horizon.
- Do not change profile directory layout.
- Do not optimize subprocess startup here; H10 owns that.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Filesystem_Call_Audit.md`
- `H_02_Phase_02_Command_Snapshot_Model.md`
- `H_03_Phase_03_Profile_Account_Indexing.md`
- `H_04_Phase_04_Diagnostics_Status_Reuse.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Filesystem_Budget_Verification.md`
- `V_02_Snapshot_Verification.md`
- `V_03_Index_Invalidation_Verification.md`
- `V_04_Acceptance_Matrix.md`
