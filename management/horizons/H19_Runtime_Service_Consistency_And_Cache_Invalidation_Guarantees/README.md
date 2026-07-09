# H19 Runtime Service Consistency And Cache Invalidation Guarantees

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Guarantee that service-backed execution and one-shot execution produce
equivalent results and that cached runtime state is invalidated after mutations.

## Goals

- Define a formal runtime cache ownership and invalidation contract.
- Prove service-backed and one-shot read-only commands return equivalent output.
- Ensure mutating commands notify or bypass the service consistently.
- Audit runtime service requests, fallback, and invalidation through H14.
- Strengthen service lifecycle diagnostics and stale socket cleanup.

## Completion Notes

- Added a runtime service contract covering state ownership, never-cache state,
  eligible commands, ineligible commands, and mutation-to-domain invalidation.
- Added structured invalidation reason/domain payloads, persisted last
  invalidation diagnostics, idempotent generation updates, and audit events.
- Extended service diagnostics with availability, unavailable reason, recovery
  hints, stale cleanup auditing, and the runtime contract.
- Verified service-backed equivalence for `config show --json`,
  `list agy --json`, `status agy p1 --json`, and `diagnostics agy --json`.
- Verified with `pytest -q`: 116 passed.
- Verified validation commands: service status JSON and diagnostics JSON.

## Non-Goals

- Do not make the runtime service mandatory.
- Do not route high-risk mutating commands through the service by default.
- Do not expose any TCP or remote IPC surface.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Runtime_State_Inventory.md`
- `H_02_Phase_02_Invalidation_Contract.md`
- `H_03_Phase_03_Execution_Equivalence_And_Fallback.md`
- `H_04_Phase_04_Service_Diagnostics_Audit_And_Recovery.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Invalidation_Verification.md`
- `V_02_Equivalence_Verification.md`
- `V_03_Acceptance_Matrix.md`
