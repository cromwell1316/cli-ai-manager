# H34 Log Tail And Developer Mode Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make developer mode cheap enough to leave enabled while preserving useful live
diagnostics.

## Goals

- Avoid reading hundreds of log lines on every render.
- Track file offset or bounded tail state.
- Keep filtering for quota, AGY, failures, and errors.
- Handle log rotation or truncation.
- Preserve redaction boundaries.

## Non-Goals

- Do not add an external log service.
- Do not change audit storage.
- Do not print raw token-like values.

## Work Areas

- Add a small log tail cache keyed by path, inode, size, and offset.
- Refresh only when file size changes.
- Keep selected diagnostic lines pre-filtered for the render loop.
- Add tests for missing, truncated, and growing log files.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "developer or log or interactive"
python3 scripts/benchmark_runtime.py --scenario status-redraw
```

Acceptance target: developer mode does not materially increase redraw time.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Log_Tail_Baseline.md`
- `H_02_Phase_02_Incremental_Tail_Cache.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
