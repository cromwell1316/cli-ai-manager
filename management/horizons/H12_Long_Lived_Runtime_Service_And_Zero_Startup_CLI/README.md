# H12 Long Lived Runtime Service And Zero Startup CLI

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

If H10 proves host Python startup remains the dominant cost after lazy imports,
introduce an optional long-lived local runtime that serves fast commands without
starting a fresh Python process for every interaction.

## Goals

- Design an optional local runtime service for hot commands.
- Keep normal one-shot CLI behavior as the default fallback.
- Use a local-only IPC mechanism with strict permission checks.
- Reuse live profile snapshots, metadata, diagnostics, and quota scheduler state
  safely across commands.
- Add explicit lifecycle commands for start, stop, status, and restart.

## Non-Goals

- Do not require a daemon for basic CLI use.
- Do not expose network APIs.
- Do not store raw tokens in the service state.
- Do not implement this before H10 and H11 show that a long-lived runtime is
  justified.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Daemon_Justification_And_Architecture.md`
- `H_02_Phase_02_Local_IPC_And_Permissions.md`
- `H_03_Phase_03_Runtime_State_And_Invalidation.md`
- `H_04_Phase_04_CLI_Client_And_Fallback.md`
- `H_05_Phase_05_Operational_Lifecycle.md`
- `H_06_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_IPC_Verification.md`
- `V_02_Runtime_State_Verification.md`
- `V_03_Fallback_Verification.md`
- `V_04_Acceptance_Matrix.md`
