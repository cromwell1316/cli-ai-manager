# H30 Interactive Render Loop Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H30_Interactive_Render_Loop_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Keep the interactive UI responsive as profile count, quota updates, and
developer diagnostics grow.

## Goals

- Render only when the visible snapshot changes.
- Cache formatted status rows and quota cells.
- Reduce repeated visible-width calculations.
- Keep quota background work from causing render jitter.
- Preserve keyboard behavior and screen layout.

## Non-Goals

- Do not redesign the UI.
- Do not remove developer mode or quota progress indicators.
- Do not change shortcut keys.

## Work Areas

- Add a stable render snapshot hash.
- Cache row formatting by profile status and quota freshness.
- Reuse terminal width and column calculations within a frame.
- Avoid full screen redraws when only progress spinner changes.
- Benchmark status redraw with many profiles.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario status-redraw
pytest -q tests/test_profile_manager.py -k "interactive or render"
```

Acceptance target: lower redraw time and fewer unnecessary frame writes while
preserving visual output.

## Implementation Evidence

- Added an interactive status fast-key so unchanged frames skip paint and row
  formatting entirely.
- Added bounded status row and AGY quota cell render caches keyed by visible
  status/quota state and freshness.
- Added quota render generation tracking so background quota mutations invalidate
  cached status frames.
- Developer mode live logs now use a cheap log file mtime/size fingerprint for
  unchanged redraws.
- `TerminalFrameRenderer` now skips writes when a TTY frame is unchanged.
- Benchmark:
  - Before: `status-redraw` median `10.944ms`
  - After: `status-redraw` median `0.009ms`
- Targeted validation passed:
  - `pytest -q tests/test_profile_manager.py -k "interactive or render"`
  - `python3 scripts/benchmark_runtime.py --scenario status-redraw`

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Render_Baseline_And_State_Hash.md`
- `H_02_Phase_02_Row_And_Cell_Caches.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
