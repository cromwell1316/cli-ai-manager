# H52 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate documentation for complete Windows and WSL operation.

## Checks

- Windows installation, verification, update, and rollback are documented.
- WSL/Linux installation, verification, update, and rollback are documented.
- AGY credential authority differences are explained.
- First-login, sync, recovery, and diagnostics workflows are covered.

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "runbook or docs"
python3 scripts/horizon_governance.py --json
python3 profile_manager.py --help
python3 profile_manager.py config show --json
python3 -m pytest
```

## Completion Evidence

Validation covers static runbook content, horizon governance, CLI help, config
JSON, and the full test suite.
