# H_03 Phase 03 Platform Renderer Adapters

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Implement renderer adapters for WSL raw-key interaction and native Windows
prompt-based interaction.

## Work

- Keep Unix terminal dependencies out of Windows imports.
- Keep Windows fallback behavior deterministic under tests.
- Preserve WSL screen clearing, theme reset, and child CLI release behavior.

## Exit Criteria

Both adapters render the same semantic menu and return the same action IDs.

