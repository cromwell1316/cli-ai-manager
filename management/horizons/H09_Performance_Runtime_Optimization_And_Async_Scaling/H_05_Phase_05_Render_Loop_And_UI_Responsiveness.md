# H_05 Phase 05 Render Loop And UI Responsiveness

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Keep interactive screens responsive while background quota jobs are active.

## Scope

- Add render snapshots so expensive display strings are computed once per data
  change, not every wake tick.
- Separate status collection, quota state merge, and terminal rendering.
- Avoid full-screen redraws when only the countdown changes, unless terminal
  simplicity makes full redraw cheaper and still within budget.
- Add fake-terminal tests for redraw count and visible width.
- Keep colored email/quota rendering stable.
- Preserve stale quota values and white stale coloring.

## Acceptance

- Status redraws stay under the agreed budget with 12 visible profiles.
- Redraws do not perform profile discovery, metadata reads, or AGY log scans.
- Countdown refreshes at a useful cadence without busy-looping.
- Keyboard shortcuts remain responsive while workers are active.
