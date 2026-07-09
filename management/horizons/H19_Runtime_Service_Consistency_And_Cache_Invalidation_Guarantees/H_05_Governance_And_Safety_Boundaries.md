# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- IPC must remain local-only.
- Service execution must be optional.
- Mutating commands must not be routed through service without a separate safety
  decision.
- Cache invalidation must be idempotent.
- Service diagnostics must not leak secrets.
