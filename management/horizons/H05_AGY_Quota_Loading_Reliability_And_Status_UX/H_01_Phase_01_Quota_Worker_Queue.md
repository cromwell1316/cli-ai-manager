# H_01 Phase 01 Quota Worker Queue

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Replace per-render thread spawning with a reusable quota scheduler. The
scheduler must enqueue quota refresh work and process it with bounded
concurrency.

## Requirements

- Add an interactive quota scheduler owned by `cli_profile_manager/interactive.py`
  or a new small module such as `cli_profile_manager/quota_scheduler.py`.
- Default AGY concurrency must be bounded, initially `2`.
- Allow override through `AI_MAN_INTERACTIVE_AGY_QUOTA_CONCURRENCY`.
- Deduplicate queued work by `(tool_key, profile_num)` so repeated screen
  refreshes do not create duplicate jobs.
- Keep status rendering nonblocking; queue operations must be constant-time from
  the renderer's perspective.
- Track job state separately from quota state:
  - `idle`
  - `queued`
  - `running`
  - `ready`
  - `retryable`
  - `failed`
- Preserve compatibility with current `ensure_quota_loading()` callers until
  the renderer is migrated.

## Acceptance

- A test proves that scheduling 11 AGY profiles starts no more than the configured
  concurrency at once.
- A test proves that repeated `ensure_quota_loading("agy", 1)` calls create one
  queued/running job, not many.
- A test proves that account status can be collected without waiting for quota
  workers to finish.
