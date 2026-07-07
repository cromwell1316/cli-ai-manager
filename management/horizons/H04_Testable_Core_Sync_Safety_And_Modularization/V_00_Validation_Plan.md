# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Commands

```bash
python3 -m py_compile profile_manager.py tests/test_profile_manager.py
python3 -m pytest tests/test_profile_manager.py
python3 profile_manager.py status codex bad --json
python3 profile_manager.py launch codex p1 --dry-run --json
python3 profile_manager.py import codex requirements-dev.txt p1 --dry-run --json
python3 profile_manager.py sync --from wsl --mode hard --dry-run --json
./scripts/verify_no_tui_surface.sh
```

## Evidence Required

- pytest passes with isolated temporary profile homes.
- JSON error payloads parse as JSON and preserve exit codes.
- Sync dry-run reports delete paths without mutating destination files.
- Launch dry-run prints a plan and does not execute the target CLI.
- Import/export dry-run JSON payloads report planned paths without writing credentials.
