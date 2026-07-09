# H_02 Phase 02 Invalidation Contract

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make cache invalidation explicit and testable.

## Scope

- Add invalidation reasons and affected domains.
- Emit invalidation after metadata writes, profile changes, sync, import/export,
  clear, label, config changes, and audit retention changes where relevant.
- Make invalidation idempotent.
- Record invalidation in diagnostics and audit.

## Acceptance

- Every mutating command has an invalidation test.
- Invalidation is safe when the service is absent or unhealthy.
- Diagnostics show last invalidation reason and time.
