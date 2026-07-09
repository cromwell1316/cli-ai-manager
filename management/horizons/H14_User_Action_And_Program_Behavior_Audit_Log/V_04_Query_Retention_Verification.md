# V_04 Query Retention Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Verify `audit status` reports backend, path, record count, retention, and last
  write health.
- Verify `audit list` filters by time, category, command, tool, profile, result,
  and correlation ID.
- Verify `audit show` can inspect both event IDs and correlation IDs.
- Verify `audit export` produces valid redacted JSONL and JSON.
- Verify retention and purge behavior for JSONL and SQLite.

## Evidence

- `audit status`, `audit list`, `audit show`, `audit export`, `audit compact`,
  and `audit purge` are implemented.
- `audit list` supports filters for category, command, tool, profile, result,
  correlation ID, and ISO timestamp bounds.
- `test_audit_cli_records_command_and_supports_query_export_purge` verifies
  list/export/purge through the CLI.
- Retention compaction supports age and maximum-byte limits for JSONL and
  SQLite backends.
