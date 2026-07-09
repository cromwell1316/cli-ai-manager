# H_01 Phase 01 Render Surface Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H15_Terminal_Rendering_Engine_And_Interactive_UX_Stability/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Identify every interactive render path and decide which paths need diff redraw,
plain print behavior, or one-shot prompts.

## Scope

- Inventory menus, status screens, sync screens, import/export screens, launch
  screens, error screens, and confirmation prompts.
- Classify screens as static, live, prompt-driven, or subprocess handoff.
- Identify shared layout primitives: header, menu, table, footer, message line,
  and confirmation block.
- Document terminal control sequences currently used.

## Acceptance

- Every render path has an owner and migration decision.
- Existing full-clear behavior is documented before replacement.
- Non-TTY behavior is explicitly defined.
