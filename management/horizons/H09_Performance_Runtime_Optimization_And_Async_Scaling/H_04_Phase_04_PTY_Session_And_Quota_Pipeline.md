# H_04 Phase 04 PTY Session And Quota Pipeline

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Reduce quota probe latency while preserving reliable terminal-mode parsing.

## Scope

- Profile AGY/Codex/Claude PTY startup, command-send, post-command wait, and
  idle detection separately.
- Replace fixed waits where possible with readiness detection based on prompt or
  stable terminal output.
- Add idle/session TTL and max-session count for persistent quota sessions.
- Track session health and parser miss history per profile.
- Avoid reading and reparsing unbounded terminal output.
- Bound `raw_summary` and diagnostics output size.
- Keep retry and session invalidation behavior deterministic.

## Acceptance

- Warm persistent-session quota probes are measurably faster than cold probes.
- Timeout and parser-miss recovery remains covered by deterministic tests.
- Session cleanup is verified for clear/sync/logout and process-exit cases.
- No token-like values are logged or included in diagnostics.
