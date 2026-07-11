# H41 Executable Lookup Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Cache repeated executable lookups in hot paths where `shutil.which` is called
with the same command and environment.

## Goals

- Cache executable discovery per process.
- Key the cache by command name and `PATH`.
- Preserve behavior when `PATH` changes.
- Keep failures and missing executables represented exactly as before.

## Non-Goals

- Do not persist executable paths across manager runs.
- Do not bypass explicit executable paths.
- Do not change command launch semantics.

## Work Areas

- Find repeated executable lookup sites in quota, process policy, and command
  startup paths.
- Centralize lookup caching behind a small helper.
- Add tests for cache hits, misses, and `PATH` invalidation.
- Measure affected startup and quota warm-path scenarios.

## Implementation

- Added `cli_profile_manager.executable_lookup.executable_path`.
- Cache key is `(command, PATH)` for ordinary command names.
- Missing executable results are cached as `None`.
- Explicit executable paths are resolved through `shutil.which` without cache.
- Integrated the helper into diagnostics, quota backend discovery, quota process
  startup, process policy backend checks, and launch CLI availability checks.
- Added `reset_executable_lookup_cache` for deterministic tests.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or process or executable"
pytest -q tests/test_executable_lookup_cache.py
pytest -q tests/test_quota_warm_path.py
python3 scripts/benchmark_runtime.py --scenario all
```

Acceptance target: repeated lookups with the same `PATH` avoid duplicate
filesystem scans while preserving existing launch behavior.

## Validation Results

- `python3 -m pytest -q tests/test_executable_lookup_cache.py`: 4 passed.
- `python3 -m pytest -q tests/test_quota_warm_path.py`: 4 passed.
- `python3 -m pytest -q tests/test_profile_manager.py -k "quota or process or executable"`:
  91 passed, 98 deselected.
- `python3 scripts/benchmark_runtime.py --scenario all`: completed.
  Representative medians: `parse-args` 5.802ms, `command-config-json` 2.073ms,
  `command-diagnostics-agy-json` 3.986ms, `quota-warm-mock` 0.234ms.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Lookup_Surface_Inventory.md`
- `H_02_Phase_02_Cached_Executable_Discovery.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
