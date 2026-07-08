# H_01 Phase 01 Status Retry Refresh Loop

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make interactive status screens keep refreshing while retryable quota work is
scheduled for the near future, even when no quota worker is currently running.

## Scope

- Add a helper that returns the next quota wake-up deadline for a tool.
- Use that deadline in `view_status()` when choosing `get_key()` timeout.
- Avoid busy loops; cap refresh interval to a small predictable value only while
  there is active or retryable quota work.
- Keep Enter, Esc, q, and Ctrl+C behavior unchanged.

## Acceptance

- A failed quota probe with `next_retry_at` wakes the screen automatically after
  backoff expires.
- A fully idle screen with no retryable work still blocks normally for input.
- Tests prove the timeout calculation for active, retryable, and idle states.
