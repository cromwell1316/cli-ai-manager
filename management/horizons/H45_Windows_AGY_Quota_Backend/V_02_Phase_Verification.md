# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | Command model and backend boundary reviewed against current quota call sites. |
| Phase 02 | Windows helper-integrated quota runner covered by unit tests. |
| Phase 03 | Diagnostics, docs, and full quota regression suite pass. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "quota or windows_agy"
python3 scripts/horizon_governance.py --json
```
