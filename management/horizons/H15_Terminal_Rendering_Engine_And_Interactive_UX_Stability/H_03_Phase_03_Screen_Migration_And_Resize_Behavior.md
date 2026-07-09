# H_03 Phase 03 Screen Migration And Resize Behavior

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Move interactive screens onto the shared renderer and handle terminal size
changes consistently.

## Scope

- Migrate status, menus, sync progress, and confirmation screens.
- Rebuild table layouts around measured terminal width.
- Add resize detection for live loops.
- Preserve keyboard shortcuts and existing workflow behavior.
- Keep subprocess handoff screens simple and readable.

## Acceptance

- Live screens no longer flicker during background updates.
- Narrow terminals keep all text coherent.
- Resize triggers a full frame repaint rather than broken partial output.

## Evidence

- `render_status_screen()` and `run_menu()` now render complete frame lines and
  hand them to `TerminalFrameRenderer`.
- Resize detection compares terminal size between frames and forces a full
  repaint.
- Existing narrow table and visible-width tests continue to pass.
