# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: horizon brief

Status: planned.

## Problem

The current quota subsystem is structurally better than the pre-H05 version, but
it still has runtime failure modes:

- A status screen can stop refreshing after all active jobs finish, even if
  retry backoff will soon expire.
- A timed-out persistent PTY session can stay alive and be reused in a corrupted
  terminal state.
- `unknown` hides whether there was no output, a parser miss, an auth prompt, or
  a changed CLI layout.
- Some behaviors are only indirectly tested through happy-path fakes.

## Desired End State

The quota subsystem should recover by itself in a long-running interactive
manager session. Failed probes should be classified, retries should wake the
screen at the right time, and broken PTY sessions should be discarded before
they poison later requests.

## Exit Criteria

- Retryable quota entries cause the status screen to wake and reschedule work
  when `next_retry_at` is reached.
- Persistent sessions are closed and replaced after timeout/process-exit class
  failures.
- Parser misses and empty output are distinct quota states.
- Unit tests cover refresh-loop timing, PTY reset, failure taxonomy, and stale
  preservation.
