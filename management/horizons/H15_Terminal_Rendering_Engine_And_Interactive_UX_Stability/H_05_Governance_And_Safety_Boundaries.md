# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Rendering changes must not change command results.
- Non-TTY output must remain suitable for logs and scripts.
- New live screens must use the shared renderer.
- Escape sequences must be centralized and tested.
- Cursor restoration must be protected by `finally` blocks or context managers.
