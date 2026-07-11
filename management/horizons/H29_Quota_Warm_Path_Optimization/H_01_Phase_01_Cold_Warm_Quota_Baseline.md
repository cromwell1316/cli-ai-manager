# H_01 Phase 01 Cold Warm Quota Baseline

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Separate session startup cost from repeated quota snapshot cost.

## Deliverables

- Cold startup metric.
- Warm `/usage` metric.
- Parser and capture timing.
- Failure-state baseline.

## Result

- Warm snapshot metrics are recorded on tmux sessions.
- Persistent session diagnostics expose latency, capture mode, capture count,
  bytes captured, and marker readiness.
- Parser benchmark remains fast: median `0.230ms`, p95 `0.307ms`.
