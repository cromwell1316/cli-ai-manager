# H38 Fast Diagnostics Health Split

Owner: cli-profile-manager
Source of Truth: management/horizons/H38_Fast_Diagnostics_Health_Split/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Keep fast diagnostics on the fast path by avoiding live health probes that are
only needed for deep diagnostics.

## Goals

- Preserve diagnostics JSON shape for existing consumers.
- Avoid process backend checks in fast diagnostics mode.
- Keep deep diagnostics behavior unchanged.
- Add regression coverage for fast-vs-deep health collection.

## Non-Goals

- Do not remove health data from deep diagnostics.
- Do not change configuration semantics.
- Do not hide real configuration errors.

## Work Areas

- Route fast diagnostics through the effective config payload without live
  health checks.
- Keep full health payload construction behind deep diagnostics mode.
- Add tests that fail if fast diagnostics calls process backend probing.
- Re-measure diagnostics benchmark after the split.

## Validation

```bash
pytest -q tests/test_config_fast_path.py
python3 scripts/benchmark_runtime.py --scenario command-execute
```

Acceptance target: fast diagnostics avoids live process backend checks while
deep diagnostics still reports full health data.

## Implementation Result

- Fast diagnostics now builds configuration data through the non-live effective
  config path.
- Deep diagnostics keeps the full live config health path.
- Regression tests cover both the fast no-probe contract and the deep health
  contract.
- Runtime benchmark evidence was captured with `command-diagnostics-agy-json`
  median at 65.947ms in the validation run.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Diagnostics_Mode_Boundary.md`
- `H_02_Phase_02_Fast_Path_Regression_Guards.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
