# H52 Docs Operational Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Create a complete operational runbook for installing and using the manager on
both Windows and WSL.

## Goals

- Document native Windows installation, verification, rollback, and update.
- Document WSL/Linux installation, verification, rollback, and update.
- Explain AGY credential authority differences between WSL OAuth files and
  Windows Credential Manager backups.
- Provide first-login flows for `p1`, `p2`, and `p3`.
- Provide sync direction examples and recovery procedures.
- Clearly list known limitations, especially native Windows AGY quota and
  concurrent sessions until those horizons are complete.

## Non-Goals

- Do not duplicate every CLI help string.
- Do not include real account names or token material.
- Do not claim unsupported Windows behavior is fully implemented.

## Work Areas

- Add or reorganize README sections for Windows, WSL, sync, and recovery.
- Add a short quickstart and a detailed troubleshooting section.
- Add examples for `ai-man login`, `launch`, `import`, `export`, `sync`, and
  diagnostics.
- Cross-link relevant horizon documents.

## Validation

```bash
python3 scripts/horizon_governance.py --json
python3 profile_manager.py --help
python3 profile_manager.py config show --json
```

Acceptance target: a user can complete Windows and WSL setup from the docs
without relying on the external AGY multi-account notes.

## Files

- `README.md`
