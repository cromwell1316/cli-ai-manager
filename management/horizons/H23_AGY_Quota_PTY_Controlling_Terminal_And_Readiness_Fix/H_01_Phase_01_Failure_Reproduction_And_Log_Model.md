# H_01 Phase 01 Failure Reproduction And Log Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Turn the observed `!` behavior into a reproducible failure model before changing
the PTY implementation.

## Scope

- Capture current `ai-man quota agy p1 --json` failure shape.
- Document audit events for `process_exit`, `retry_wait`, and quota job retries.
- Document relevant AGY log markers:
  - `CLI ready for user input`
  - `CLI program exited, shutting down`
  - `error opening TTY`
  - `You are not logged into Antigravity`
  - `Account ineligible`
  - `RESOURCE_EXHAUSTED`
  - `quotaRefreshLoop`
- Define which markers are terminal failures and which are recoverable startup
  churn.

## Acceptance

- A failing current-run sample is documented.
- Failure states map to user-facing diagnostics.
- The implementation has a concrete before/after target.
