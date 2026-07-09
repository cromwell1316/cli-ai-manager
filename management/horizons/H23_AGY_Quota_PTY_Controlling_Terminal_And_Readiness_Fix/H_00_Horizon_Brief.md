# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

Interactive AGY status currently shows `!` for quota cells when background
quota jobs fail. Recent audit and native AGY logs show the dominant failure is
`process_exit` during startup, even for profiles whose OAuth credentials are
valid.

## Problem

The current quota PTY launcher provides stdin/stdout/stderr through a slave PTY
but does not explicitly make that PTY the controlling terminal. AGY/Bubble Tea
is TTY-sensitive and AGY `1.1.0` may also start helper/server processes,
perform silent auth, and briefly exit wrapper paths before the probe sends
`/usage`. Generic idle detection treats this as failure, so every profile lands
in retry state and the UI shows `!`.

## Strategy

Replace the AGY quota startup path with a robust PTY session launcher and
AGY-specific readiness detection. Send `/usage` only after ready output is
observed. Classify known AGY startup and account conditions explicitly, preserve
stale usable quota values, and add fake-CLI tests that reproduce the TTY and
readiness behavior without live AGY.
