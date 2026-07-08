# H07 Operational Observability And Live Validation

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Add enough operational visibility to understand quota and profile behavior on a
real machine without exposing secrets or forcing users to inspect logs by hand.

## Goals

- Add a diagnostics command that summarizes quota scheduler, cache, sessions,
  profile homes, and recent failures.
- Add safe debug logging for quota probes and session recovery.
- Add live validation scripts for AGY status across multiple profiles.
- Record validation evidence without storing tokens or raw credential material.
- Make README troubleshooting actionable.

## Non-Goals

- Do not upload telemetry.
- Do not log token contents, OAuth refresh tokens, or full credential JSON.
- Do not add a daemon or background service.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Diagnostics_Command.md`
- `H_02_Phase_02_Safe_Debug_Logging.md`
- `H_03_Phase_03_Live_AGY_Validation_Scripts.md`
- `H_04_Phase_04_Troubleshooting_Docs.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Diagnostics_Command_Verification.md`
- `V_02_Logging_Verification.md`
- `V_03_Live_Validation_Verification.md`
- `V_04_Documentation_Verification.md`
- `V_05_Acceptance_Matrix.md`
