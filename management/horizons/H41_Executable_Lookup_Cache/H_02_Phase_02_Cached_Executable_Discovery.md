# H_02 Phase 02 Cached Executable Discovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Implement cached executable discovery in selected hot paths.

## Deliverables

- Small helper for cached executable lookup.
- Tests for hits, misses, and `PATH` invalidation.
- Integration into selected process policy or quota paths.
- Benchmark evidence for affected scenarios.

## Implementation Notes

- Preserve `None` results for missing commands.
- Do not normalize or rewrite explicit executable paths.
- Keep cache process-local and easy to reset in tests.
