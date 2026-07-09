# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 profile_manager.py diagnostics --json
python3 profile_manager.py audit status --json
python3 profile_manager.py audit list --json --limit 10
```

## Manual Validation

```bash
python3 profile_manager.py list agy
python3 profile_manager.py status agy p1
python3 profile_manager.py audit list --command status
python3 profile_manager.py audit show <correlation-id>
python3 profile_manager.py audit export --format jsonl
```

## Evidence Requirements

- Event schema and redaction evidence.
- File backend and SQLite backend write/read evidence.
- Coverage evidence for command, interactive, quota, runtime, sync, and
  subprocess flows.
- Retention and purge evidence.
- Diagnostics evidence for audit health and backend failures.
