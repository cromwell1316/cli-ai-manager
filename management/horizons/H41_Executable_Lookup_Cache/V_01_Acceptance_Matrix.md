# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Cache key | Lookup result is keyed by executable and `PATH` | `tests/test_executable_lookup_cache.py::test_executable_lookup_cache_hits_for_same_path` |
| Invalidation | Changed `PATH` causes a fresh lookup | `tests/test_executable_lookup_cache.py::test_executable_lookup_cache_key_tracks_path` |
| Missing results | Missing executable results are preserved and cached as `None` | `tests/test_executable_lookup_cache.py::test_executable_lookup_cache_preserves_missing_results` |
| Explicit paths | Explicit executable paths bypass the cache | `tests/test_executable_lookup_cache.py::test_executable_lookup_explicit_paths_are_not_cached` |
| Behavior | Missing and explicit executables behave as before | `tests/test_profile_manager.py -k "quota or process or executable"` |
| Performance | Repeated lookup cost is reduced | `python3 scripts/benchmark_runtime.py --scenario all` |
