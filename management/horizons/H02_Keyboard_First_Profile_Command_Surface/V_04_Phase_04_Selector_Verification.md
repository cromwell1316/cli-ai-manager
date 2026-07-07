# V_04 Phase 04 Selector Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
python3 -m py_compile profile_manager.py
rg -n "def run_menu|def get_key|launch_account|import_credential|export_credential" profile_manager.py
rg -n "textual|rich|curses" profile_manager.py
```

## Pass Criteria

- Selector remains standard-library only.
- Selector dispatches to the same command functions used by noninteractive mode.
- Keyboard actions are bounded and do not resize or corrupt profile data.
