# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Cache key | Lookup result is keyed by executable and `PATH` | Cache key tests |
| Invalidation | Changed `PATH` causes a fresh lookup | Invalidation tests |
| Behavior | Missing and explicit executables behave as before | Existing process/quota tests |
| Performance | Repeated lookup cost is reduced | Benchmark output |
