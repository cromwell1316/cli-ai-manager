# H_02 Phase 02 Worker Scheduler And Backpressure

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make quota scheduling predictable under many profiles and repeated refreshes.

## Scope

- Define queue priorities, coalescing, cancellation, and forced refresh rules.
- Limit concurrent work per tool and globally.
- Add backpressure behavior for repeated refresh keys.
- Ensure retry timers cannot create tight loops.
- Add metrics for queued, started, completed, failed, coalesced, and cancelled.

## Acceptance

- Scheduler behavior is deterministic in tests.
- Repeated manual refreshes do not create duplicate jobs.
- Backoff and refresh timers are bounded and observable.
