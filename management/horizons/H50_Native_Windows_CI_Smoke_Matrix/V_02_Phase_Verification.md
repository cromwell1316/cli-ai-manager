# V_02 Phase Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Verification Matrix

| Phase | Verification |
| --- | --- |
| Phase 01 | CI scope excludes real credentials and destructive operations. |
| Phase 02 | Windows CI job runs syntax, tests, installer smoke, and helper checks. |
| Phase 03 | Local reproduction docs and governance checks are updated. |

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Completion Evidence

Phase verification is implemented by the Windows smoke workflow, the local
PowerShell smoke script, focused Windows tests, and horizon governance.
