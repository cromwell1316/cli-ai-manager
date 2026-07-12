# H_03 Phase 03 Lock And Recovery Flows

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: phase

Status: completed.

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

## Implementation Notes

- Missing or invalid launch backups are blocked before invoking the PowerShell
  helper and include login/restore/diagnostics recovery commands.
- Existing helper mutex contention messaging remains explicit about same-user
  serialization and separate Windows users for true parallel isolation.
- `AI_MAN_AGY_SLOT_LOCK_TIMEOUT_SECONDS` is documented as a configurable
  same-user wait, not parallel isolation.
