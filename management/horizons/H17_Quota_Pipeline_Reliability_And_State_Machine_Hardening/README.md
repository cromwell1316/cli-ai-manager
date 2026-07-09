# H17 Quota Pipeline Reliability And State Machine Hardening

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Make quota loading deterministic, recoverable, observable, and safe under
parallel profile refreshes and flaky native CLIs.

## Goals

- Replace implicit quota state transitions with a documented state machine.
- Harden worker queues, retry/backoff, stale cache reuse, and invalidation.
- Bound PTY sessions and persistent quota sessions with reliable cleanup.
- Add deterministic tests for concurrency, timeout, parser miss, auth failure,
  and process exit paths.
- Integrate audit and diagnostics for quota lifecycle events.

## Completion Notes

- Implemented explicit runtime quota pipeline states, legal transition
  validation, failure taxonomy, diagnostics exposure, and audit transition
  events.
- Preserved existing CLI quota output compatibility while adding
  `machine_state`, `state_machine`, and `pipeline_state` diagnostics.
- Verified with `pytest -q`: 103 passed.
- Verified quota-parser benchmark and diagnostics JSON commands from the
  validation plan.

## Non-Goals

- Do not change native CLI quota commands unless required for correctness.
- Do not store raw PTY buffers or unredacted quota output.
- Do not make quota probing mandatory for read-only status commands.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_State_Model_And_Failure_Taxonomy.md`
- `H_02_Phase_02_Worker_Scheduler_And_Backpressure.md`
- `H_03_Phase_03_PTY_Session_Lifecycle_Hardening.md`
- `H_04_Phase_04_Diagnostics_Audit_And_Test_Harness.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_State_Machine_Verification.md`
- `V_02_Runtime_Verification.md`
- `V_03_Acceptance_Matrix.md`
