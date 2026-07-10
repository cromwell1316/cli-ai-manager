# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

AGY quota refresh originally used a persistent PTY session so `/usage` could be
sent to an interactive CLI. After AGY CLI 1.1.1, bare PTY startup no longer
matches a real terminal closely enough. The CLI can remain stuck in sign-in
bootstrap even when profile tokens are present and manual terminal launches
work.

The observed manual launch path is:

```bash
export HOME="/home/olivercromwell/agy-homes/p1"
exec /home/olivercromwell/.local/bin/agy "$@"
```

The important behavior is that only `HOME` changes. The terminal context remains
a real interactive terminal, and `cwd` remains a normal working directory.

## Problem

The current Python PTY backend provides file descriptors and a controlling TTY,
but it is not a terminal emulator. AGY emits terminal capability query escape
sequences and expects terminal responses. Without those responses, AGY can stay
in:

```text
Welcome to the Antigravity CLI. You are currently not signed in.
Signing in...
```

This is not evidence that tokens are missing. It is evidence that the runtime
context differs from a real terminal enough to break AGY bootstrap.

## Strategy

Use tmux as the default AGY quota backend when available. tmux supplies the
terminal behavior AGY expects while still allowing the manager to create
profile-isolated, background, persistent sessions. Keep the existing Python PTY
backend as fallback for systems without tmux and for non-AGY tools.

## Success Criteria

- AGY quota sessions start with profile `HOME` and normal `cwd`.
- AGY reaches prompt in tmux despite eligibility warning output.
- `/usage` is sent only after readiness.
- Quota output is parsed from tmux pane capture.
- False `auth_required` states disappear for token-bearing profiles.
- Real login failures remain visible.
- No orphaned manager-owned tmux sessions remain after cleanup.
