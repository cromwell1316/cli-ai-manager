# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Problem

`profile_manager.py` now owns CLI parsing, interactive menus, credential
conversion, metadata, rendering, platform detection, launch, and sync. Changes
to direct commands can accidentally break interactive flows, and changes to sync
or credential conversion can silently affect real profile data.

## Strategy

Build the test layer first, then harden sync and JSON contracts, then extract
modules in small steps. The target package layout is:

```text
profile_manager/
├── cli.py
├── interactive.py
├── tools.py
├── credentials/
│   ├── agy.py
│   ├── codex.py
│   └── claude.py
├── sync.py
├── metadata.py
└── paths.py
```

## Success Criteria

- The H02/H03 core behavior is covered by pytest fixtures with isolated homes.
- Hard sync refuses destructive mutation without `--yes`.
- `sync --dry-run --json` reports copied, skipped, converted, invalid, and
  would-delete paths.
- Status JSON includes `has_token`, `token_state`, `credential_source`,
  `account`, and `warnings`.
- Import/export/sync/launch dry-run expose stable JSON success and error payloads.
- Module extraction preserves existing direct-command exit codes.
