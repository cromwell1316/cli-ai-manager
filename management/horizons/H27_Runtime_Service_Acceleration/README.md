# H27 Runtime Service Acceleration

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make the optional runtime service the fastest path for frequent read-only
commands while keeping one-shot CLI behavior as the reliable fallback.

## Goals

- Accelerate `list`, `status`, `config`, and safe diagnostics through service reuse.
- Reuse metadata, path resolution, profile discovery, and command snapshots.
- Preserve mutation invalidation guarantees.
- Keep local-only IPC and strict permissions.
- Keep service use optional.

## Non-Goals

- Do not serve mutating commands through cached state.
- Do not include live quota probing in service fast paths by default.
- Do not expose network APIs.

## Work Areas

- Benchmark service-backed commands against one-shot commands.
- Cache read-only state with explicit generation counters.
- Tighten invalidation after `login`, `import`, `clear`, `sync`, and `label`.
- Add service health metrics for cache hit/miss and request latency.
- Improve fallback when the service is stale or unavailable.

## Validation

```bash
python3 profile_manager.py service start
python3 profile_manager.py list agy --json
python3 profile_manager.py status agy p1 --json
python3 profile_manager.py service stop
pytest -q tests/test_profile_manager.py -k "service"
```

Acceptance target: service-backed read-only commands avoid repeated cold-start
work and remain output-equivalent to one-shot commands.
