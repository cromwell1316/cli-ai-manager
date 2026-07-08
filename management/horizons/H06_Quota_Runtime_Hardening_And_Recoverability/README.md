# H06 Quota Runtime Hardening And Recoverability

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Turn quota probing from a best-effort background feature into a recoverable
runtime subsystem. H05 added queueing, stale cache, persistent sessions, and AGY
columns; H06 closes the remaining reliability gaps around automatic retry,
broken PTY reuse, precise failure classification, and predictable shutdown.

## Goals

- Keep interactive status screens refreshing when retry backoff expires.
- Reset persistent PTY sessions after timeout, process exit, or repeated parser
  failures.
- Split quota failures into actionable states such as `empty_output`,
  `parser_miss`, `timeout`, `auth_required`, `missing_cli`, and `process_exit`.
- Make cache, retry, session lifetime, and queue behavior deterministic enough
  to test without real CLIs.
- Prevent stale successful quota values from being erased by failed refreshes.
- Keep the UI readable while exposing enough diagnostics for debugging.

## Non-Goals

- Do not replace native CLI probing with unofficial APIs.
- Do not make status rendering wait for quota probes.
- Do not introduce persistent on-disk quota cache in this horizon.
- Do not broaden Windows Credential Manager mutation behavior.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Status_Retry_Refresh_Loop.md`
- `H_02_Phase_02_PTY_Session_Recovery.md`
- `H_03_Phase_03_Failure_Taxonomy_And_Diagnostics.md`
- `H_04_Phase_04_Deterministic_Runtime_Tests.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Retry_Refresh_Verification.md`
- `V_02_Session_Recovery_Verification.md`
- `V_03_Failure_Taxonomy_Verification.md`
- `V_04_Runtime_Testing_Verification.md`
- `V_05_Acceptance_Matrix.md`

## Related Assets

- `cli_profile_manager/interactive.py`
- `cli_profile_manager/quota.py`
- `cli_profile_manager/cli.py`
- `tests/test_profile_manager.py`
- `management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX`
