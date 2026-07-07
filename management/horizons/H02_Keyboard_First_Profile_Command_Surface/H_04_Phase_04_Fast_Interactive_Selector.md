# H_04 Phase 04 Fast Interactive Selector

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Scope

Keep a lightweight selector for users who prefer visual profile selection, while
ensuring it is still standard-library only.

## Required Behavior

- Launching `ai-man` without subcommands opens the selector.
- The selector uses the Phase 01 keymap.
- The selector calls the same command functions as noninteractive commands.
- Screen redraw stays simple and fast; no Textual/Rich/curses dependency.

## Phase Exit

Interactive and noninteractive paths produce the same status, launch, import,
export, label, and clear behavior.
