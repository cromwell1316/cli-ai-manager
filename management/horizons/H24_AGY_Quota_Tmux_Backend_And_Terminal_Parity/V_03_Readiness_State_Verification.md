# V_03 Readiness State Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Eligibility Warning

Input:

```text
Eligibility Check
not currently available in your location
>
? for shortcuts
```

Expected:

```text
ready
```

The warning must not prevent `/usage`.

## Startup Sign-In Text

Input:

```text
Welcome to the Antigravity CLI. You are currently not signed in.
Signing in...
```

while session is alive and startup window has not expired.

Expected:

```text
startup_pending
```

## Sign-In Timeout

Input remains stuck on sign-in text past startup timeout.

Expected:

```text
auth_required
```

with a diagnostic summary.

## Resource Exhausted

Input:

```text
You have exhausted your capacity on this model.
Your quota will reset after ...
```

Expected:

```text
resource_exhausted
```

This state must win over eligibility warning text if both appear in the session.

## Prompt Ready

Input:

```text
Antigravity CLI 1.1.1
...
>
? for shortcuts
```

Expected:

```text
ready
```
