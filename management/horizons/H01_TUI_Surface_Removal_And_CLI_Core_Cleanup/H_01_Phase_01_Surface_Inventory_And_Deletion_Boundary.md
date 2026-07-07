# H_01 Phase 01 Surface Inventory And Deletion Boundary

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Inventory every TUI entrypoint, import, documentation reference, and launcher
before deleting anything.

## Required Inventory

- Python TUI files: `tui_manager.py` in WSL and Windows prototype paths.
- Windows launchers: `Start-TUI.bat` and any shortcuts that invoke it.
- Imports: `textual`, `rich`, and TUI-only widgets/screens.
- Documentation claims that mention TUI, Textual, Rich, or zero dependencies.
- Installer links that imply TUI support.

## Boundary

Credential homes and saved tokens are not implementation surface. They must be
excluded from deletion even if they contain generated caches, logs, or copied
prototype files.

## Phase Exit

The removable file list and protected-data list are explicit before Phase 02
deletes or edits runtime files.
