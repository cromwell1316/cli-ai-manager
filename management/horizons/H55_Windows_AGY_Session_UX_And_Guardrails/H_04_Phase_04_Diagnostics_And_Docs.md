# H_04 Phase 04 Diagnostics And Docs

Owner: cli-profile-manager
Source of Truth: management/horizons/H55_Windows_AGY_Session_UX_And_Guardrails/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Extend diagnostics and runbook coverage for Windows AGY guardrails.

## Work

- Add token-safe diagnostics fields for backup/live-slot state.
- Document lock contention and separate Windows user guidance.
- Add regression tests for warning text and recovery routing.

## Exit Criteria

The operational runbook and diagnostics agree on Windows AGY behavior.

## Implementation Notes

- `docs/OPERATIONAL_RUNBOOK.md` now documents shared-slot preflight, missing
  backup recovery, lock contention, and separate-user isolation guidance.
- Regression tests cover guardrail text, launch blocking, interactive warning
  output, and token-safe diagnostics.
