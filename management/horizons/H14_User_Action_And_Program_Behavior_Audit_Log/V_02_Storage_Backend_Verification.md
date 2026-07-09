# V_02 Storage Backend Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Verify JSONL append behavior and recovery from malformed rows.
- Verify SQLite schema creation, migrations, inserts, queries, and retention
  deletes.
- Verify user-only permissions for audit directories and files.
- Verify backend fallback and diagnostics when writes fail.
- Verify strict mode behavior separately from default best-effort behavior.

## Evidence

- `test_audit_jsonl_backend_writes_and_skips_malformed_rows` verifies JSONL
  append, malformed-row recovery, and `0o700`/`0o600` permissions.
- `test_audit_sqlite_backend_writes_and_queries` verifies SQLite schema
  creation, insert, query filters, and status reporting.
- Default audit writes are best-effort; `AI_MAN_AUDIT_STRICT=1` is the explicit
  mode for propagating backend failures.
- `python3 profile_manager.py audit status --json` reports backend, storage
  path, permissions, retention, and record count.
