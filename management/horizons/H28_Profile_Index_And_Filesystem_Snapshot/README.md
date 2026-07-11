# H28 Profile Index And Filesystem Snapshot

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Reduce repeated filesystem scanning across `list`, `status`, `diagnostics`, and
interactive status screens.

## Goals

- Build command-scoped and service-scoped profile indexes.
- Reuse occupied profile lists, display lists, credential existence checks, and
  AGY account lookup results.
- Keep indexes invalidated by file mtimes or mutation commands.
- Avoid caching raw credential contents.
- Preserve correctness when profile files change between commands.

## Non-Goals

- Do not introduce a persistent database.
- Do not change profile directory layout.
- Do not hide invalid or missing credential files.

## Work Areas

- Count filesystem calls on representative profile roots.
- Extend `CommandSnapshot` or add a dedicated `ProfileIndex`.
- Store profile home, credential path, token state, account, warnings, and mtimes.
- Share the index across diagnostics and status rendering.
- Add tests for invalidation after profile changes.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "snapshot or status or diagnostics"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

Acceptance target: fewer repeated `os.listdir`, `exists`, and JSON reads per
command with unchanged status payloads.

## Implementation Evidence

- Added command-scoped `ProfileIndex` with profile discovery, display slots,
  credential path facts, account path facts, and filesystem mtime/size
  fingerprints.
- Wired `CommandSnapshot` to reuse indexed profile lists, status payloads, AGY
  account lookups, and file existence facts across list/status/diagnostics.
- Runtime service now invalidates its command snapshot and response cache when
  indexed profile file fingerprints become stale between service commands.
- Raw credential contents are read only during status parsing and are not stored
  in the profile index.
- Benchmark after implementation:
  - `command-config-json` median: `52.019ms`
  - `command-list-agy-json` median: `7.443ms`
  - `command-status-agy-json` median: `6.969ms`
  - `command-diagnostics-agy-json` median: `43.780ms`
- Targeted H28 validation passed:
  - `pytest -q tests/test_profile_manager.py -k "snapshot or status or diagnostics"`
  - `python3 scripts/benchmark_runtime.py --scenario command-execute`

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Filesystem_Call_Baseline.md`
- `H_02_Phase_02_Profile_Index_Model.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
