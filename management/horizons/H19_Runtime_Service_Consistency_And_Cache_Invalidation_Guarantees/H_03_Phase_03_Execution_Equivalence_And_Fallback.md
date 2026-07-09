# H_03 Phase 03 Execution Equivalence And Fallback

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Prove that service-backed commands behave like one-shot commands.

## Scope

- Compare JSON and text output for eligible commands.
- Compare exit codes and errors.
- Verify fallback when service is stopped, unhealthy, stale, or incompatible.
- Ensure config resolution is equivalent between execution modes.

## Acceptance

- Equivalence tests cover list, status, config, and diagnostics.
- Fallback preserves command semantics.
- Service errors do not hide command-level errors.
