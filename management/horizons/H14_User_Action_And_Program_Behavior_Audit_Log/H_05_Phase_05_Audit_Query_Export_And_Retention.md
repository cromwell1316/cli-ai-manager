# H_05 Phase 05 Audit Query Export And Retention

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Provide user-facing tools to inspect, export, compact, and purge audit data.

## Scope

- Add `audit status` to report backend, storage path, record count, retention,
  and last write health.
- Add `audit list` with filters for time range, category, command, tool,
  profile, result, and correlation ID.
- Add `audit show <event-id|correlation-id>` for detailed local inspection.
- Add `audit export --format jsonl|json` with the same redaction defaults as
  storage.
- Add `audit purge` and retention configuration by age and maximum storage size.
- Add diagnostics integration for audit health and storage permissions.

## Acceptance

- Audit data can be inspected without opening raw files manually.
- Exported data preserves event schema and redaction.
- Retention can remove old records from both JSONL and SQLite backends.
- Purge commands require explicit confirmation unless `--yes` is supplied.
