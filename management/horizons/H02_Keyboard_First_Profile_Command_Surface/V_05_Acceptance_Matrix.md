# V_05 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: acceptance matrix

Status: implemented.

| Phase | Acceptance Evidence |
| --- | --- |
| Phase 01 Command Model | Help output, README, and keymap agree |
| Phase 02 Profile Discovery | First-free profile numbering works and invalid IDs fail |
| Phase 03 Commands And Exit Codes | Direct commands are scriptable and return meaningful exit codes |
| Phase 04 Selector | Interactive selector is fast, standard-library only, and shares command logic |

## Done Definition

H02 is complete when every common profile operation is available as a direct
command, the interactive selector is only a thin keyboard layer over those
commands, profile numbering is correct, and the entire surface is testable
without TUI dependencies.
