# H_04 Phase 04 Status Table Quota UX

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Keep the AGY status table readable while quota values are loading, stale,
refreshing, or failed.

## Requirements

- Keep separate AGY quota columns:
  - `FM` for Gemini Flash Medium
  - `FH` for Gemini Flash High
  - `FL` for Gemini Flash Low
  - `PL` for Gemini Pro Low
  - `PH` for Gemini Pro High
  - `CS` for Claude Sonnet
  - `CO` for Claude Opus
- Add discovered extra pools as additional compact columns after the defaults.
- Render only percentages in quota cells, for example `94%` or `100%`.
- Render job markers compactly:
  - `...` for queued/running with no previous data
  - `~` next to stale values when refresh is running
  - `!` for failed refresh with no previous data
- Keep detailed warnings out of the table body.
- Keep account, status, quota columns, and label aligned with ANSI color codes.
- Keep no-token rows blank in quota columns.

## Acceptance

- A test proves available AGY quotas render into separate columns.
- A test proves no-token rows do not show `no_token` inside quota columns.
- A test proves stale rows show old percentages and a refresh marker.
- A test proves failed rows show `!` without shifting following columns.
