# V_01 Backend Selection Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Cases

## Auto With tmux Present

Given `AI_MAN_AGY_QUOTA_BACKEND` is unset or `auto`, and `tmux` exists in
`PATH`, AGY quota uses tmux.

Expected:

```text
backend=tmux
```

## Auto Without tmux

Given `AI_MAN_AGY_QUOTA_BACKEND=auto`, and `tmux` is not found, AGY quota falls
back to persistent PTY.

Expected:

```text
backend=persistent_pty
```

and a diagnostic warning that tmux was unavailable.

## Forced PTY

Given:

```bash
AI_MAN_AGY_QUOTA_BACKEND=pty
```

AGY quota uses persistent PTY even if tmux is installed.

## Forced tmux Missing

Given:

```bash
AI_MAN_AGY_QUOTA_BACKEND=tmux
```

and tmux is unavailable, AGY quota returns a clear missing backend state instead
of silently falling back.

## Non-AGY Tools

Codex and Claude should not use tmux because this horizon is scoped to AGY
terminal parity.
