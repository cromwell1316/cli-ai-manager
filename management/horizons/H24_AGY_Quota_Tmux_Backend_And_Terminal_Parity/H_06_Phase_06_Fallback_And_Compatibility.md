# H_06 Phase 06 Fallback And Compatibility

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Preserve compatibility for environments without tmux and keep existing quota
behavior for other tools.

## Fallback Rules

When:

```text
AI_MAN_AGY_QUOTA_BACKEND=auto
```

use tmux if available, otherwise persistent PTY.

When:

```text
AI_MAN_AGY_QUOTA_BACKEND=pty
```

always use persistent PTY.

When:

```text
AI_MAN_AGY_QUOTA_BACKEND=tmux
```

require tmux and return a clear missing backend error if tmux is unavailable.

## Compatibility Rules

- Codex remains on current PTY quota behavior.
- Claude remains on current PTY quota behavior.
- Existing parser output shape remains unchanged.
- Existing JSON schema remains compatible.
- Existing UI states remain compatible, but false AGY `auth_required` should be
  reduced.

## Rollback

Rollback without code changes:

```bash
export AI_MAN_AGY_QUOTA_BACKEND=pty
```

This must restore the previous AGY PTY path for debugging.

## Diagnostics

Diagnostics should report:

- configured AGY quota backend;
- resolved AGY quota backend;
- tmux binary path, if present;
- active manager-owned tmux session count;
- persistent PTY session count.

## Risks

- Silent fallback from tmux to PTY can confuse debugging. In `auto`, fallback is
  acceptable but must be logged.
- Forced tmux mode should not silently fall back.
