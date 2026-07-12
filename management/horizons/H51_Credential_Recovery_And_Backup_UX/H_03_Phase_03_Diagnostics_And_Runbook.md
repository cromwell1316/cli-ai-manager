# H_03 Phase 03 Diagnostics And Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document and expose recovery state clearly.

## Deliverables

- Diagnostics for managed backups and live slot state.
- Recovery examples in README/runbook.
- Troubleshooting notes for missing or corrupt backups.

## Validation Focus

- Users can identify the active and restorable account safely.
- Docs cover rollback from common mistakes.

## Completion Evidence

- `ai-man diagnostics agy --json` includes `agy_credential_recovery` with
  managed backup validity, account metadata, saved timestamps, and paths.
- README documents restore/set/save/clear recovery examples and dry-run usage.
- Troubleshooting behavior is covered for missing, invalid, and non-native live
  slot operations.
