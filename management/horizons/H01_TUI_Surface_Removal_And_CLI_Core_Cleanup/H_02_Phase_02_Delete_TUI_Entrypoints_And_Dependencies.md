# H_02 Phase 02 Delete TUI Entrypoints And Dependencies

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Remove supported TUI execution paths and dependency imports.

## Required Changes

- Delete or archive `tui_manager.py` from the active application surface.
- Remove Windows `Start-TUI.bat` from the supported launcher set.
- Remove `textual` and `rich` imports from supported code.
- Ensure the remaining executable path is `profile_manager.py` through
  `ai-man`, `profile-man`, and `pman`.
- Add a lightweight guard check that fails if supported files import `textual`
  or `rich`.

## Phase Exit

The project can be installed and launched without Textual/Rich present.
