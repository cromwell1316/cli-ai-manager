# H_02 Phase 02 State Cache And Invalidation

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Cache read-only state inside the service with clear generations.

## Deliverables

- Metadata/path/profile cache.
- Generation counters.
- Mutation invalidation tests.
- Service latency metrics.

## Result

- Successful `config`, `list`, and `status` service responses are cached by argv.
- Read-only service execution reuses one generation-scoped `CommandSnapshot`.
- Each invalidation increments the service generation and clears cached entries.
- The service observes external invalidation files before serving cached runs.
- Health metrics expose entries, hits, misses, hit rate, invalidations, and
  request latency.
