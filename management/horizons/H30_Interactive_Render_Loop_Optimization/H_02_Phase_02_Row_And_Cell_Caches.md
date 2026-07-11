# H_02 Phase 02 Row And Cell Caches

Owner: cli-profile-manager
Source of Truth: management/horizons/H30_Interactive_Render_Loop_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Cache expensive row formatting and visible-width calculations.

## Deliverables

- Status row cache.
- Quota cell cache.
- Per-frame terminal width reuse.
- Render regression tests.

## Result

Status rows and AGY quota cells are cached by visible render state. Unchanged
TTY frames are skipped before writing, while changed frames still use the
existing line-diff renderer.
