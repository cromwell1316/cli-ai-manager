# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | UI snapshots cover labels and shortcuts. |
| Phase 02 | Action-route tests cover menu dispatch. |
| Phase 03 | Terminal hygiene tests cover shell reset and child CLI release. |
| Phase 04 | CI runs focused cross-platform UI checks. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

