# V_01 Renderer Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Initial paint uses a full frame.
- Subsequent paints update only changed lines.
- Shrinking frames clear stale content.
- Cursor visibility is restored after exits and exceptions.
- Non-TTY mode emits readable text.

## Evidence

- `tests/test_profile_manager.py::test_terminal_frame_renderer_initial_diff_shrink_and_resize`
  verifies initial paint, diff paint, shrink cleanup, and resize repaint.
- `tests/test_profile_manager.py::test_terminal_frame_renderer_restores_cursor_after_exception`
  verifies cursor cleanup on exceptions.
- `tests/test_profile_manager.py::test_terminal_frame_renderer_non_tty_avoids_control_sequences`
  verifies plain non-TTY output.
