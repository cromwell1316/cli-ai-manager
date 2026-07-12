# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | Layout documents app files, shims, helper, and profiles. |
| Phase 02 | Shims point at Windows-local application files. |
| Phase 03 | Update and rollback preserve profile data. |
| Phase 04 | CI and runbook cover local and UNC install modes. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

