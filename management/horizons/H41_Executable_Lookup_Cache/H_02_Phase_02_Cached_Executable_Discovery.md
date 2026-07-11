# H_02 Phase 02 Cached Executable Discovery

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

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

## Implementation

- Added `cli_profile_manager/executable_lookup.py` with:
  - `executable_path(command, path=None)`
  - `executable_lookup_cache_key(command, path=None, environ=None)`
  - `reset_executable_lookup_cache()`
- Ordinary command names use a process-local dictionary keyed by command and
  effective `PATH`.
- Explicit paths are resolved directly and are not stored in the cache.
- Replaced selected repeated `shutil.which` calls in quota, process policy,
  diagnostics, and launch startup checks.

## Tests

- `tests/test_executable_lookup_cache.py` covers cache hit, missing-result
  caching, `PATH` invalidation, and explicit-path bypass.
- Existing quota/process tests were kept behavior-focused by patching the new
  lookup boundary in the modules under test.
