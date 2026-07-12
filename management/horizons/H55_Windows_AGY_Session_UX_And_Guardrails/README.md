# H55 Windows AGY Session UX And Guardrails

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make native Windows AGY behavior clear and safe around the shared Credential
Manager slot while preserving the best available profile workflow.

## Goals

- Explain shared-slot limitations in the launch and login surfaces.
- Show active profile, backup credential, and live-slot status before risky
  actions.
- Add recovery guidance when the live slot is stale, missing, or locked.
- Keep same-user concurrent AGY sessions serialized with explicit messaging.
- Document separate Windows users as the true parallel-isolation boundary.

## Non-Goals

- Do not claim same-user native Windows AGY has true parallel isolation.
- Do not bypass Windows Credential Manager.
- Do not expose OAuth token blobs in UI, logs, or tests.

## Phases

- Phase 01: map AGY launch/login/recovery states.
- Phase 02: add user-facing warnings and status summaries.
- Phase 03: add lock contention and recovery flows.
- Phase 04: extend diagnostics and runbook coverage.

## Verification

```bash
python3 -m pytest tests/test_profile_manager.py -k "agy and windows"
python3 -m pytest
```

Acceptance target: users understand when Windows AGY is serialized, how to
recover the live slot, and when separate Windows users are required.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_State_Model.md`
- `H_02_Phase_02_User_Facing_Warnings.md`
- `H_03_Phase_03_Lock_And_Recovery_Flows.md`
- `H_04_Phase_04_Diagnostics_And_Docs.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
