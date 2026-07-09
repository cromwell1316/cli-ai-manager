# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- New settings must be registered centrally.
- Config output must redact sensitive values by default.
- Invalid config must not silently select dangerous behavior.
- Environment compatibility must be maintained unless explicitly deprecated.

## Implementation Evidence

New config display and diagnostics flow through the central registry. Invalid
values produce warnings and safe fallbacks, and configured secret-like values
are redacted before display.
