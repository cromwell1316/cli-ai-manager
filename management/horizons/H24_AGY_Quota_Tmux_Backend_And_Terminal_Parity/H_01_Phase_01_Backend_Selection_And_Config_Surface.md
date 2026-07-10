# H_01 Phase 01 Backend Selection And Config Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Introduce explicit AGY quota backend selection without disturbing existing
Codex and Claude quota paths.

## Required Behavior

- Add an AGY-specific backend selector.
- Default to `auto`.
- In `auto`, prefer tmux when `tmux` is available.
- Fall back to persistent Python PTY when tmux is unavailable or disabled.
- Allow forced modes for debugging and rollback.

## Configuration

Add or document:

```text
AI_MAN_AGY_QUOTA_BACKEND=auto|tmux|pty
```

Default:

```text
auto
```

Resolution:

```text
auto + tmux present  => tmux
auto + tmux missing  => pty
tmux + tmux missing  => missing_backend quota failure
pty                  => current persistent PTY backend
```

## Implementation Notes

- Keep `quota_probe_command("agy", n)` as `["agy"]`.
- Keep `quota_probe_env("agy", n)` using profile `HOME`.
- Keep `quota_probe_cwd("agy", n)` as `os.getcwd()`.
- Route backend choice inside quota runner selection, not inside parser logic.
- Keep non-AGY tools on current persistent PTY behavior.

## Logging

Every AGY quota session creation must log:

```text
tool=agy backend=<tmux|persistent_pty> cwd=<cwd> home=<home>
```

## Risks

- A hidden global switch could make debugging harder. The selected backend must
  appear in logs and diagnostics.
- Forced `tmux` mode should fail clearly if tmux is unavailable.
