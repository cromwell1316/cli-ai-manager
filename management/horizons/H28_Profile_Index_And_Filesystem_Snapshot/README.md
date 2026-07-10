# H28 Profile Index And Filesystem Snapshot

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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
