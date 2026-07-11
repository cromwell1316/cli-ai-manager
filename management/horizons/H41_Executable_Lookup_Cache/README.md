# H41 Executable Lookup Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or process or executable"
python3 scripts/benchmark_runtime.py --scenario all
```

Acceptance target: repeated lookups with the same `PATH` avoid duplicate
filesystem scans while preserving existing launch behavior.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Lookup_Surface_Inventory.md`
- `H_02_Phase_02_Cached_Executable_Discovery.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
