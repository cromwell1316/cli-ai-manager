# H_05 Phase 05 Lifecycle Cleanup And Eviction

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Ensure manager-owned tmux quota sessions do not leak and do not interfere with
manual user sessions.

## Registry

Track tmux sessions by the same dimensions used for persistent quota sessions:

- tool key
- command
- absolute `cwd`
- profile `HOME`
- relevant tool home variables

The registry should store:

- tmux session name
- created time
- last used time
- readiness state
- parser miss count
- starting flag

## Cleanup Events

Close tmux sessions when:

- process exits through `atexit`;
- user invalidates a profile;
- profile token is removed;
- session TTL expires;
- max session count is exceeded;
- session is dead;
- parser miss threshold is exceeded;
- backend state is corrupt or unreadable.

## Eviction

Honor:

```text
AI_MAN_QUOTA_SESSION_TTL_SECONDS
AI_MAN_QUOTA_SESSION_MAX
```

Do not evict a starting session during its startup window unless it is dead or
has exceeded a hard timeout.

## Kill Scope

Only run:

```bash
tmux kill-session -t <session>
```

for manager-owned session names created by this backend.

Never run broad tmux cleanup commands such as killing all sessions.

## Logging

Log:

```text
quota session create
quota session reuse
quota session ready
quota session evict
quota session close
quota session invalidate
```

Include:

- tool
- backend
- session name
- cwd
- home
- reason

## Risks

- Killing a user session would be a serious regression. Prefix and ownership
  checks are mandatory.
- Keeping dead sessions in the registry can stall quota refresh. Liveness checks
  must be cheap and reliable.
