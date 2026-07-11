# H27 Runtime Service Acceleration

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

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

## Implementation Notes

- Runtime service caches successful read-only `config`, `list`, and `status`
  responses by argv inside the live service process.
- Runtime service reuses one generation-scoped `CommandSnapshot` for service
  read-only execution, amortizing metadata, profile discovery, account parsing,
  and status assembly.
- Cache entries are scoped to the current service generation and are cleared by
  explicit mutation invalidation or externally observed invalidation files.
- Health output now reports cache entries, hit/miss counts, invalidations,
  hit rate, and request latency metrics.
- `diagnostics` remains service-eligible but is not response-cached, so generated
  timestamps and dynamic diagnostic state stay fresh.

## Evidence

```bash
python3 -m py_compile cli_profile_manager/runtime_service.py cli_profile_manager/cli.py
pytest -q tests/test_profile_manager.py -k "runtime_service or service"
pytest -q tests/test_profile_manager.py -k "not test_in_process_command_perf_budgets"
```

Result: service/runtime `16 passed, 156 deselected`; broad suite `171 passed, 1 deselected`.

Manual socket validation confirmed health cache metrics after repeated
service-backed `list agy --json`: `entries=1`, `hits=1`, `misses=1`,
`snapshot_cached=true`, `snapshot_builds=1`.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Service_Baseline_And_Command_Eligibility.md`
- `H_02_Phase_02_State_Cache_And_Invalidation.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
