# H_02 Phase 02 Preflight And Confirmation API

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Build shared APIs for preflight checks, confirmation prompts, and operation
results.

## Scope

- Add operation descriptors with command name, risk, tool, profile, and target.
- Add preflight result objects for planned creates, updates, deletes, external
  launches, and skipped actions.
- Add confirmation helpers for CLI flags and interactive prompts.
- Add standard cancellation and refusal result codes.
- Emit H14 audit events for preflight, confirmation, cancellation, and result.

## Acceptance

- Mutating commands can use the same confirmation path.
- Dry-run output is consistent across CLI and JSON modes.
- Cancellation is not treated as an internal error.
