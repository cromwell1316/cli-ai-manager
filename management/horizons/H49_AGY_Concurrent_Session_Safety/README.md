# H49 AGY Concurrent Session Safety

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Determine and harden the safe concurrency model for multiple native Windows AGY
sessions that share the single Credential Manager target `gemini:antigravity`.

## Goals

- Reproduce staggered parallel launches for `agy1`, `agy2`, and `agy3`
  equivalents.
- Detect whether AGY rereads or refreshes the shared Credential Manager slot
  after startup.
- Add warnings or guardrails if concurrent sessions can cross accounts.
- Document recovery steps for restoring the intended credential slot.
- Decide whether separate Windows users are required for true parallel
  isolation.

## Non-Goals

- Do not claim true Windows AGY parallel isolation until verified.
- Do not bypass Windows Credential Manager security boundaries.
- Do not store unencrypted extra token copies beyond managed backups.

## Work Areas

- Add a manual and optional automated concurrency drill.
- Add diagnostics that reports the active live slot account when available.
- Add user-facing warning text for native Windows concurrent AGY launches.
- Evaluate a lock, stagger, or confirmation policy for risky launches.

## Validation

```powershell
ai-man login agy p1
ai-man login agy p2
ai-man launch agy p1
ai-man launch agy p2
ai-man diagnostics agy --json --show-accounts
```

Acceptance target: the project has an evidence-backed policy for parallel AGY
sessions on Windows, including clear user warnings and recovery commands.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Concurrency_Drill_Design.md`
- `H_02_Phase_02_Diagnostics_And_Live_Slot_Inspection.md`
- `H_03_Phase_03_Policy_Warnings_And_Recovery.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
