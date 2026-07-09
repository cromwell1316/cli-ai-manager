# H_03 Phase 03 Runtime State And Invalidation

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Keep cached runtime state fast and correct.

## Scope

- Cache profile discovery and metadata with file timestamp checks.
- Reuse quota scheduler state where appropriate.
- Invalidate caches after login, import, export, clear, sync, and label changes.
- Avoid storing raw credential data.
- Bound memory use and stale state lifetime.

## Acceptance

- State invalidation tests cover every mutating command.
- Service memory stays within documented limits.
