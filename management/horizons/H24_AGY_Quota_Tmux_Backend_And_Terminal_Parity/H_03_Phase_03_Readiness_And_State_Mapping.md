# H_03 Phase 03 Readiness And State Mapping

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Make AGY readiness reflect terminal reality instead of treating transient
bootstrap text as immediate authentication failure.

## Ready States

Treat AGY as ready when captured tmux pane output contains a stable prompt such
as:

```text
>
? for shortcuts
```

or other known AGY ready markers.

## Non-Fatal Startup Text

Do not fail startup solely because output contains:

```text
Eligibility Check
not currently available in your location
```

This is a warning in the observed AGY behavior.

Do not immediately fail startup solely because output contains:

```text
You are currently not signed in.
Signing in...
```

During startup this is a pending bootstrap state. It becomes a failure only when
it persists past the configured startup window and the session cannot be used.

## State Mapping

Use:

```text
startup_pending
```

when AGY is still starting and the session is alive.

Use:

```text
auth_required
```

only when AGY explicitly requires user login or cannot complete sign-in after
the readiness budget has expired.

Use:

```text
account_ineligible
```

only as a warning for AGY eligibility text unless it is the only terminal output
and no prompt appears.

Use:

```text
resource_exhausted
```

when AGY reports quota/capacity exhaustion.

## Timing

Honor:

```text
AI_MAN_AGY_QUOTA_STARTUP_SECONDS
```

Default should remain conservative enough for AGY cold startup. The tmux backend
should not kill a session just because it is still bootstrapping unless the
session is clearly unusable or expired.

## Risks

- Being too tolerant can hide real login failures.
- Being too strict returns to false `auth_required`.

The distinction must be based on prompt readiness, explicit login instructions,
and elapsed startup budget.
