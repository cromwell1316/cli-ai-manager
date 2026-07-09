# H_04 Phase 04 Service Diagnostics Audit And Recovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: implementation phase

Status: completed.

## Objective

Make runtime service failures and recovery paths easy to understand.

## Scope

- Add service health details to diagnostics.
- Record request, response, fallback, shutdown, and stale cleanup events in H14
  audit.
- Improve stale socket and pid cleanup.
- Provide user-facing recovery hints.

## Acceptance

- Diagnostics explain why service execution is unavailable.
- Stale runtime files can be cleaned safely.
- Audit reconstructs service request paths.
