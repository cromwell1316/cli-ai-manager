# H_01 Phase 01 Horizon Lifecycle And Evidence Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: implementation phase

Status: completed.

## Lifecycle Model

- `planned`: scope exists, implementation has not started.
- `active`: implementation is in progress.
- `implemented`: code or documentation changes are present and validation is
  expected to pass.
- `completed`: implementation, validation evidence, and acceptance updates are
  recorded.
- `verified`: completed work has an additional independent review or release
  verification.
- `blocked`: progress is intentionally stopped by an external dependency.
- `deferred`: scope remains valid but is no longer scheduled.

Acceptance matrix status vocabulary should use `Planned`, `Implemented`,
`Completed`, `Verified`, `Blocked`, `Deferred`, or a short evidence phrase such
as `Verified through full command test suite`.

## Objective

Define how horizons move from planned to implemented to verified.

## Scope

- Define lifecycle states and required evidence.
- Define acceptance matrix status vocabulary.
- Define required files for a complete horizon.
- Define when README and validation docs must be updated.

## Acceptance

- Lifecycle rules are documented.
- Evidence requirements are concrete.
- Acceptance matrix statuses are standardized.
