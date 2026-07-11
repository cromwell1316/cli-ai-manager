# H39 Process Policy Backend Check Cache

Owner: cli-profile-manager
Source of Truth: management/horizons/H39_Process_Policy_Backend_Check_Cache/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Cache expensive process backend capability checks inside a single process so
repeated config, diagnostics, and runtime-service calls do not rerun identical
system probes.

## Goals

- Cache `systemd-run --user --scope` availability per process.
- Invalidate cache when relevant environment inputs change.
- Preserve fallback behavior when systemd is unavailable.
- Keep tests deterministic with explicit cache reset hooks.

## Non-Goals

- Do not persist process policy decisions across processes.
- Do not force systemd usage.
- Do not change configured backend precedence.

## Work Areas

- Identify cache key inputs such as `PATH`, `XDG_RUNTIME_DIR`, and explicit
  backend settings.
- Add a small in-process cache around systemd user-scope availability.
- Expose a test-only reset path consistent with existing module patterns.
- Add benchmark and unit coverage for repeated calls.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "process or config or diagnostics"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

Acceptance target: repeated health/config checks in one process perform at most
one identical systemd capability probe per cache key.

Completed evidence:

- Added process-local systemd user-scope probe cache with environment-sensitive
  key and reset hook.
- Added cache hit, reset, and environment invalidation unit coverage.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Cache_Key_And_Reset_Contract.md`
- `H_02_Phase_02_Process_Policy_Cache_Integration.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
