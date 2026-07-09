# V_01 Renderer Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Verification

- Initial paint uses a full frame.
- Subsequent paints update only changed lines.
- Shrinking frames clear stale content.
- Cursor visibility is restored after exits and exceptions.
- Non-TTY mode emits readable text.
