# H_02 Phase 02 Persistent AGY Sessions

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Make repeated AGY quota refreshes reuse the same live CLI process for a profile
within the current manager process.

## Requirements

- Keep one persistent PTY session per `(tool_key, profile_home, command, env)`
  cache key.
- Start the session lazily on first quota refresh.
- Reuse the session for later `/usage` refreshes when the process is alive.
- Restart the session if the process exits, the PTY closes, or output becomes
  unusable.
- Close all live sessions through `atexit` and explicit invalidation hooks.
- Do not share one AGY PTY between different profiles because AGY reads profile
  credentials from `HOME`.
- Keep one-shot noninteractive quota probing available for tests and manual
  diagnostics.

## Acceptance

- A test proves two refreshes for one profile create one PTY session.
- A test proves two different profiles create two independent sessions.
- A test proves a dead session is removed and replaced.
- A test proves `invalidate_quota_cache("agy", n)` can also close the matching
  live session.
