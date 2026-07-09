# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/verify_no_tui_surface.sh
```

## Manual Validation

```bash
python3 profile_manager.py
python3 profile_manager.py status agy p1
python3 profile_manager.py list agy
```

## Evidence Requirements

- Renderer unit tests.
- Screen migration tests.
- Manual flicker and resize validation notes.
