# H_03 Phase 03 Lock And Recovery Flows

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Objective

Provide actionable recovery when AGY backup, live slot, or mutex state blocks an
operation.

## Work

- Convert helper failures into clear app messages.
- Suggest set, save, login, or restore actions.
- Keep mutex timeout behavior configurable and documented.

## Exit Criteria

Common Windows AGY failures produce next-step guidance instead of raw helper
errors.

