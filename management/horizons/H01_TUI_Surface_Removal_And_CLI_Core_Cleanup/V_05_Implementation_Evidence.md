# V_05 Implementation Evidence

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: implementation evidence

Status: implemented.

## Evidence Log

- Removed supported WSL runtime file: `tui_manager.py`.
- Removed Windows prototype launcher: `/mnt/c/Users/Oliver/ai-man-tui-win/Start-TUI.bat`.
- Removed Windows prototype TUI file: `/mnt/c/Users/Oliver/ai-man-tui-win/tui_manager.py`.
- Rewrote `README.md` to describe the supported CLI-only workflow.
- Added `scripts/verify_no_tui_surface.sh` to fail on active TUI entrypoints or
  Textual/Rich imports in supported runtime files.
- Preserved profile data, token homes, metadata, logs, and non-TUI Windows
  prototype files.
- Validation passed:
  - `python3 -m py_compile profile_manager.py`
  - `./scripts/verify_no_tui_surface.sh`
  - `./install.sh`
  - `command -v ai-man`
  - `readlink ~/.local/bin/ai-man`
  - `readlink ~/.local/bin/profile-man`
  - `readlink ~/.local/bin/pman`

## Residuals

Intentional residual TUI references are allowed only in `management/horizons`
documents as historical planning and verification context.
