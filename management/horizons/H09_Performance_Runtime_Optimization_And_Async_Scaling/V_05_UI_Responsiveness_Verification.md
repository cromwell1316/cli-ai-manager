# V_05 UI Responsiveness Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- First paint stays within budget with fake 12-profile data.
- Redraw loop stays within budget while fake workers are active.
- Keyboard refresh and exit shortcuts are responsive during active probes.
- Colored quota and email rendering preserves visible widths.
- Countdown updates do not create a busy loop.

## Evidence

- `render_status_screen` can render from a prepared status snapshot while quota
  workers continue in the background.
- The status footer exposes active loading state, manual refresh shortcuts, and
  the automatic refresh countdown.
- Stale quota values remain visible and render white when they exceed
  `AI_MAN_INTERACTIVE_QUOTA_FRESH_SECONDS`.
- `scripts/benchmark_runtime.py --scenario status-redraw --profiles 12`
  exercises redraw cost without real CLI tokens.
- Tests cover AGY quota columns, email color rendering, percent/stale color
  rules, countdown timing, and visible-width table fitting.
