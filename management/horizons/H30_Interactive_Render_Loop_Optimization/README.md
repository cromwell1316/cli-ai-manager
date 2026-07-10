# H30 Interactive Render Loop Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H30_Interactive_Render_Loop_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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
