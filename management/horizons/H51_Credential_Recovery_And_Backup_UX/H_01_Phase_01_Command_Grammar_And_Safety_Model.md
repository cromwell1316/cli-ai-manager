# H_01 Phase 01 Command Grammar And Safety Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H51_Credential_Recovery_And_Backup_UX/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Design credential recovery command grammar and safety rules.

## Deliverables

- Commands for inspect, save, set, clear, and restore.
- Confirmation policy for live slot mutations.
- Audit event model for recovery operations.

## Validation Focus

- Mutating commands require explicit confirmation.
- Command output never includes token blobs.

## Completion Evidence

- Added `ai-man agy-credential whoami|restore|set|save|clear`.
- `restore`, `set`, `save`, and `clear` use the `agy-credential` safety policy,
  require `--yes` unless `--dry-run` is used, and emit safety payloads in JSON.
- Audit decision events are recorded for credential recovery operations.
