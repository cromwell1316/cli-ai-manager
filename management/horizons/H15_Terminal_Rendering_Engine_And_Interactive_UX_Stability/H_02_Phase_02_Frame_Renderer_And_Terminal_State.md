# H_02 Phase 02 Frame Renderer And Terminal State

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Build the reusable renderer that all live interactive screens can share.

## Scope

- Add frame buffer, line diffing, full repaint, and cleanup APIs.
- Hide and restore cursor only inside managed render sessions.
- Centralize ANSI width handling and visible truncation.
- Support terminal width discovery with deterministic fallbacks.
- Provide non-TTY output behavior that avoids escape control noise.

## Acceptance

- Renderer can update changed lines without full clear.
- Renderer restores cursor on normal exit and exceptions.
- Unit tests cover initial paint, diff paint, shrink cleanup, and non-TTY mode.
