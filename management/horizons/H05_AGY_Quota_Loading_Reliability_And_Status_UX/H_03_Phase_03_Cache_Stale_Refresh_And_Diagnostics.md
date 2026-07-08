# H_03 Phase 03 Cache Stale Refresh And Diagnostics

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Replace the current `loading`/`retry` collapse with a cache model that can show
last known quota values while refresh work continues in the background.

## Requirements

- Store quota entries with:
  - `quota`
  - `job_state`
  - `fetched_at`
  - `started_at`
  - `attempts`
  - `last_error`
  - `next_retry_at`
- Define freshness and retry settings:
  - fresh TTL default: 5 minutes
  - stale TTL default: 60 minutes
  - retry backoff default: 10 seconds, then 30 seconds, then 60 seconds
- Show fresh cached data immediately.
- Show stale cached data immediately with a refresh marker while a refresh is
  queued/running.
- Do not overwrite good stale data with `unknown`; keep the old value and attach
  the new failure diagnostic.
- Preserve detailed probe failure reasons:
  - `timeout`
  - `missing_cli`
  - `auth_required`
  - `empty_output`
  - `parser_miss`
  - `process_exit`
  - `exception`
- Keep unknown parser output available for debugging without printing long raw
  output in the status table.

## Acceptance

- A test proves stale quota values remain visible when a refresh times out.
- A test proves `unknown` does not erase the last successful quota.
- A test proves retry backoff prevents tight retry loops.
- A test proves diagnostics include both compact state and detailed warning text.
