# H02 Keyboard-First Profile Command Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Replace menu-heavy interaction with a fast keyboard command surface that works
well in WSL and Windows shells.

## Goals

- Provide direct commands for list, launch, login/add, import, export, label,
  status, clear, and sync. Done.
- Keep interactive menus optional and keyboard-fast, not TUI-dependent. Done.
- Fix profile-number selection so new installs start at `p1`, not `p13`. Done.
- Make command behavior scriptable and verifiable. Done.

## Non-Goals

- Do not add curses/Textual/Rich or mouse-oriented UI.
- Do not change the credential model owned by H03.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Command_Model_And_Keymap.md`
- `H_02_Phase_02_Profile_Discovery_And_Numbering.md`
- `H_03_Phase_03_Noninteractive_Commands_And_Exit_Codes.md`
- `H_04_Phase_04_Fast_Interactive_Selector.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Phase_01_Command_Model_Verification.md`
- `V_02_Phase_02_Profile_Discovery_Verification.md`
- `V_03_Phase_03_Command_Exit_Verification.md`
- `V_04_Phase_04_Selector_Verification.md`
- `V_05_Acceptance_Matrix.md`
- `V_06_Implementation_Evidence.md`

## Related Assets

- `profile_manager.py`
- `install.sh`
- `README.md`
