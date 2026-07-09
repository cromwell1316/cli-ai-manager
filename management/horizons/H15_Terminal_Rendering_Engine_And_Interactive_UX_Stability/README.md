# H15 Terminal Rendering Engine And Interactive UX Stability

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Make all interactive terminal screens stable, smooth, predictable, and testable
without depending on repeated full-screen clears.

## Goals

- Replace ad hoc screen clearing with one reusable terminal rendering layer.
- Use frame buffering and diff redraw for live or frequently refreshed screens.
- Preserve cursor state, terminal state, and readable output on exit or errors.
- Support terminal resize and narrow-width degradation.
- Standardize table layout, visible-width handling, ANSI stripping, and
  truncation behavior.
- Add tests for repaint behavior, text fit, keyboard loops, and non-TTY output.

## Non-Goals

- Do not reintroduce a full TUI framework in this horizon.
- Do not change command semantics or data models.
- Do not prioritize decorative UI over operational clarity.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Render_Surface_Inventory.md`
- `H_02_Phase_02_Frame_Renderer_And_Terminal_State.md`
- `H_03_Phase_03_Screen_Migration_And_Resize_Behavior.md`
- `H_04_Phase_04_UX_Regression_And_Accessibility_Checks.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Renderer_Verification.md`
- `V_02_Screen_Migration_Verification.md`
- `V_03_Acceptance_Matrix.md`
