# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H08_Distribution_Configuration_And_User_Experience_Polish/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py
./scripts/verify_no_tui_surface.sh
```

## Manual Validation

```bash
python3 profile_manager.py list agy
python3 profile_manager.py list codex
python3 profile_manager.py list claude
```

Run table checks in narrow and wide terminals.
