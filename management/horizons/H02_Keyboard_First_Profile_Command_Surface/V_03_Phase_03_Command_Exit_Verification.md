# V_03 Phase 03 Command Exit Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
python3 profile_manager.py list agy --json
python3 profile_manager.py status agy p999
python3 profile_manager.py import agy /path/that/does/not/exist p1
```

## Pass Criteria

- Valid list/status commands return `0`.
- Missing files, invalid profiles, parse failures, and missing executables return
  non-zero.
- Failed import/export leaves no partial credential file.
