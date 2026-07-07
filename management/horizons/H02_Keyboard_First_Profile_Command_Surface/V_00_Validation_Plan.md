# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: validation plan

Status: planned.

## Required Checks

```bash
python3 -m py_compile profile_manager.py
python3 profile_manager.py --help
python3 profile_manager.py list agy --json
python3 profile_manager.py list codex --json
python3 profile_manager.py list claude --json
rg -n "textual|rich|curses" profile_manager.py
```

## Required Assertions

- Help text and README command model agree.
- Empty profile stores choose `p1`.
- Direct commands and interactive selector use the same implementation functions.
- Invalid operations return non-zero.
