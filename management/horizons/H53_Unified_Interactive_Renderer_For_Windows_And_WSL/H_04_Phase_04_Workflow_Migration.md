# H_04 Phase 04 Workflow Migration

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Objective

Migrate root, tool, sync, settings, and credential recovery workflows to the
shared screen model.

## Work

- Route actions through existing operations and CLI helpers.
- Keep credential actions inside the recovery submenu.
- Verify launch, login, labels, status, clear, sync, and settings behavior.

## Exit Criteria

The old duplicated Windows routing is reduced to platform adapter code.

