# H_02 Phase 02 Shared Screen Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Define shared descriptors for screens, menu items, shortcuts, labels, and action
targets.

## Work

- Add a common model for menu definitions and action IDs.
- Preserve digit-first navigation with symbol aliases.
- Keep legacy shortcuts explicit and testable.

## Exit Criteria

Both Windows and WSL can render a representative screen from the same descriptor.
