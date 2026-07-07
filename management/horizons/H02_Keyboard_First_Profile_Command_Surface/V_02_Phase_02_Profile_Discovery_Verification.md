# V_02 Phase 02 Profile Discovery Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase verification

Status: implemented.

## Checks

```bash
python3 -m py_compile profile_manager.py
python3 profile_manager.py list agy --json
python3 profile_manager.py status agy p1
```

## Negative Fixtures

- Empty temporary `agy-homes` returns next profile `p1`.
- Existing `p1` and `p3` return next profile `p2`.
- Invalid `p0`, `p-1`, and `abc` are rejected.
- Temporary stores use `AI_MAN_AGY_HOME` and `AI_MAN_METADATA_DIR` so real
  profile data is not modified.

## Pass Criteria

Profile numbering is based on real occupied profiles, not display padding.
