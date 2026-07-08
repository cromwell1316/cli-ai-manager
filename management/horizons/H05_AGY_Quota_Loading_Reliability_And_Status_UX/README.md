# H05 AGY Quota Loading Reliability And Status UX

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Make Antigravity CLI quota loading reliable enough for daily use. The current
implementation can render account status quickly, but quota loading is too
fragile: launching all active AGY profiles at once can leave every row stuck in
`loading` or `retry`, and retry text hides the real failure mode.

## Goals

- Keep account and token status rendering immediate.
- Replace unbounded AGY quota fan-out with a bounded asynchronous work queue.
- Keep one persistent PTY session per AGY profile during the interactive manager
  session.
- Reuse fresh or stale quota results while a background refresh is running.
- Render each AGY quota pool in its own status-table column.
- Preserve diagnostic reasons for failures instead of collapsing them to
  `retry`.
- Add tests for queue behavior, cache freshness, stale display, session reuse,
  timeout diagnostics, and AGY quota-column rendering.

## Non-Goals

- Do not depend on an unofficial AGY API or scrape credentials outside profile
  homes.
- Do not block the status table while quota probes start, authenticate, or wait
  for `/usage`.
- Do not launch all AGY profiles at once by default.
- Do not remove noninteractive `quota agy pN` behavior.
- Do not change Codex or Claude quota behavior except through shared helpers
  that are proven by tests.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Quota_Worker_Queue.md`
- `H_02_Phase_02_Persistent_AGY_Sessions.md`
- `H_03_Phase_03_Cache_Stale_Refresh_And_Diagnostics.md`
- `H_04_Phase_04_Status_Table_Quota_UX.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Worker_Queue_Verification.md`
- `V_02_Persistent_Session_Verification.md`
- `V_03_Cache_Diagnostics_Verification.md`
- `V_04_Status_UX_Verification.md`
- `V_05_Acceptance_Matrix.md`

## Related Assets

- `cli_profile_manager/interactive.py`
- `cli_profile_manager/quota.py`
- `cli_profile_manager/cli.py`
- `tests/test_profile_manager.py`
- `management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization`
