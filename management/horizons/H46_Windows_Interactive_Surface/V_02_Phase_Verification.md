# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | Terminal dependency audit documents all Unix-only boundaries. |
| Phase 02 | Windows adapter tests cover key decoding and renderer startup. |
| Phase 03 | Native Windows no-args selector and direct command regression tests pass. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows"
python3 scripts/horizon_governance.py --json
```
