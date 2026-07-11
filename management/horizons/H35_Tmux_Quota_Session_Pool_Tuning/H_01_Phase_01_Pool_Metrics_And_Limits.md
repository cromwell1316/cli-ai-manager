# H_01 Phase 01 Pool Metrics And Limits

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Measure tmux session lifecycle and define safe concurrency limits.

## Deliverables

- Cold startup timing.
- Warm snapshot timing.
- Session count baseline.
- Startup and warm concurrency recommendations.

## Implementation

- `AI_MAN_TMUX_QUOTA_COLD_START_CONCURRENCY` controls tmux session creation and
  readiness waits.
- `AI_MAN_TMUX_QUOTA_WARM_SNAPSHOT_CONCURRENCY` controls concurrent warm quota
  probes.
- `persistent_quota_sessions_snapshot()` reports pool limits, backend counts,
  starting sessions, ready sessions, and per-session lifecycle metrics.
