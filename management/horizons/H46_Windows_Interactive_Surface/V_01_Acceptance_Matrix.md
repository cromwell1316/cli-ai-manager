# H46 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
|------|------------|
| Startup | Native Windows `ai-man` starts without importing Unix-only terminal modules. |
| Navigation | Numbered prompt selection works for core Windows menus. |
| Workflows | Launch, login, import, export, sync, and settings are reachable. |
| Regression | WSL/Linux selector behavior remains unchanged. |

## Evidence

- `cli_profile_manager/windows_interactive.py` contains the native Windows
  selector.
- `cli.main()` routes native Windows no-args startup to the Windows selector.
- Tests cover startup routing, selector rendering, Unix interactive import
  isolation, and launch workflow dispatch.
