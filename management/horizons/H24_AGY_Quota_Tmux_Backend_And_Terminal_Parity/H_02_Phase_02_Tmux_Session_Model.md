# H_02 Phase 02 Tmux Session Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Create a tmux-backed persistent session abstraction for AGY quota probes.

## Session Identity

Session names must be deterministic, profile-specific, and safe:

```text
ai_man_quota_agy_<profile>_<short_hash>
```

The hash should include enough identity to avoid collisions:

- tool key
- command
- absolute `cwd`
- profile `HOME`

Do not use raw paths directly in tmux session names.

## Session Startup

Startup command:

```bash
env HOME=<profile_home> agy
```

Startup `cwd`:

```text
/home/olivercromwell
```

Generalized rule: use `quota_probe_cwd("agy", n)`, which should match the
normal working directory used by manual wrapper launches.

## Required tmux Operations

- `tmux new-session -d -s <session> -c <cwd> <command>`
- `tmux has-session -t <session>`
- `tmux capture-pane -pt <session> -S <start>`
- `tmux send-keys -t <session> <keys>`
- `tmux kill-session -t <session>`

## Abstraction

Add a session class with the same conceptual API as persistent PTY sessions:

```text
start()
is_alive()
snapshot()
close()
```

The registry should be compatible with existing persistent session lifecycle
concepts, but tmux internals should not leak into parser code.

## Ownership

The manager may only kill sessions whose names it created with the
`ai_man_quota_` prefix and whose registry key matches the current session.

## Risks

- Reusing a stale tmux session from an older process can produce misleading
  output. The session model must either verify identity or create names that are
  unique enough to avoid accidental reuse.
- tmux server availability differs by environment. Backend selection must be
  explicit in logs.
