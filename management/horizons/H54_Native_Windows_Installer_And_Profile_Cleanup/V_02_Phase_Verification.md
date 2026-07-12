# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | Profile conflict detector finds stale functions and missing dot-sourced files. |
| Phase 02 | Cleanup command supports dry-run and confirmed mutation. |
| Phase 03 | Installer and verifier report Python, PATH, helper, and profile state. |
| Phase 04 | Rollback and runbook docs cover generated files and recovery. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

