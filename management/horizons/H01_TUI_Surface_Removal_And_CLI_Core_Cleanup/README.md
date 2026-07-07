# H01 TUI Surface Removal And CLI Core Cleanup

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Remove the Textual/Rich TUI surface and leave one maintained, dependency-light
command-line core. The project must stop carrying two interaction models for the
same profile operations.

## Goals

- Delete or quarantine `tui_manager.py` and Windows TUI launch assets.
- Remove Textual/Rich as runtime requirements and from documentation claims.
- Keep the pure keyboard CLI manager as the only supported local UI.
- Preserve profile data and credential files during removal.
- Add checks that prevent accidental reintroduction of the removed TUI surface.

## Non-Goals

- Do not redesign profile semantics in this horizon.
- Do not change credential formats except where required to remove TUI coupling.
- Do not delete real user profile homes or OAuth credentials.

## Files

- `H_00_Horizon_Brief.md` - problem, outcome, and success criteria.
- `H_01_Phase_01_Surface_Inventory_And_Deletion_Boundary.md` - identify removable TUI surface.
- `H_02_Phase_02_Delete_TUI_Entrypoints_And_Dependencies.md` - remove TUI code paths.
- `H_03_Phase_03_Documentation_And_Install_Cleanup.md` - align docs/install with CLI-only model.
- `H_04_Governance_And_Safety_Boundaries.md` - deletion and credential safety rules.
- `V_00_Validation_Plan.md` - full validation plan.
- `V_01_Phase_01_Surface_Inventory_Verification.md` - verification for Phase 01.
- `V_02_Phase_02_TUI_Removal_Verification.md` - verification for Phase 02.
- `V_03_Phase_03_Docs_Install_Verification.md` - verification for Phase 03.
- `V_04_Acceptance_Matrix.md` - horizon acceptance matrix.
- `V_05_Implementation_Evidence.md` - evidence log.

## Related Assets

- `profile_manager.py`
- `tui_manager.py`
- `install.sh`
- `README.md`
- `/mnt/c/Users/Oliver/ai-man-tui-win/tui_manager.py`
- `/mnt/c/Users/Oliver/ai-man-tui-win/Start-TUI.bat`
