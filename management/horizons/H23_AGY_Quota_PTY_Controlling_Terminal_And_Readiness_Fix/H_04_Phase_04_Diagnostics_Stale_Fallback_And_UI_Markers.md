# H_04 Phase 04 Diagnostics Stale Fallback And UI Markers

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make quota failures understandable and keep usable stale data visible.

## Scope

- Classify AGY quota failures into specific states or diagnostics:
  `process_exit`, `tty_unavailable`, `auth_required`, `account_ineligible`,
  `resource_exhausted`, `parser_miss`, and `timeout`.
- Add diagnostic summaries from sanitized captured output and recent AGY logs
  without persisting raw PTY buffers.
- Preserve previous successful quota values during retryable failures and show
  stale markers instead of replacing everything with `!`.
- Update interactive footer/status messages so users can distinguish stale data
  from hard failures.
- Include failure classification in diagnostics and audit events.

## Acceptance

- `!` has a clear diagnostic reason in audit/diagnostics.
- Stale successful quota values survive a later retryable AGY startup failure.
- No raw tokens or account identifiers are persisted in diagnostics.
