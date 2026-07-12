# H52 Docs Operational Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

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

## Implementation Evidence

- Added `docs/OPERATIONAL_RUNBOOK.md` as the repository-native Windows and WSL
  operations guide.
- Linked the runbook from `README.md` and added it to the project structure.
- The runbook covers install, update, verification, rollback, credential
  authority, first-login flows for `p1`, `p2`, and `p3`, sync direction, AGY
  credential recovery, diagnostics, live validation, and known limitations.
- Added a static regression test that verifies required runbook sections and
  token-safe command examples remain present.

## Validation

```bash
python3 scripts/horizon_governance.py --json
python3 profile_manager.py --help
python3 profile_manager.py config show --json
```

Acceptance target: a user can complete Windows and WSL setup from the docs
without relying on the external AGY multi-account notes.

Completed validation:

```bash
python3 -m pytest tests/test_profile_manager.py -k "runbook or docs"
python3 scripts/horizon_governance.py --json
python3 profile_manager.py --help
python3 profile_manager.py config show --json
python3 -m pytest
```

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Windows_And_WSL_Install_Runbook.md`
- `H_02_Phase_02_Profile_Workflows_And_Sync_Runbook.md`
- `H_03_Phase_03_Recovery_Diagnostics_And_Limitations.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
