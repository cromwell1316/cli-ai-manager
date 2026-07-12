# H_01 Phase 01 Terminal Dependency Audit

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Identify Unix-only assumptions in the interactive layer.

## Deliverables

- Inventory imports and call sites for `termios`, `tty`, `select`, and signal handling.
- Define platform adapter interfaces for key input and screen painting.
- Identify workflows that can share existing command operations.

## Validation Focus

- Native Windows startup avoids Unix-only imports.
- Existing WSL/Linux import behavior remains unchanged.
