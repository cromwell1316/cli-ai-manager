# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H05_AGY_Quota_Loading_Reliability_And_Status_UX/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Quota probing may launch native CLIs, but it must not mutate credential files.
- Dry-run, import, export, and sync behavior must remain unchanged.
- The scheduler must not hide authentication failures as generic retry states.
- Persistent sessions must be scoped to the manager process and closed on exit.
- Tests must not require live AGY, Codex, Claude, or network access.
- Real-output diagnostics may be used manually, but committed tests must use
  deterministic fakes.

## Operational Defaults

- AGY interactive quota concurrency: `2`.
- AGY interactive quota timeout: keep current default unless validation proves a
  better value.
- Fresh cache TTL: `300` seconds.
- Stale cache TTL: `3600` seconds.
- Status refresh interval while jobs are active: keep current half-second redraw
  unless validation shows terminal flicker or CPU issues.

## Rollback

The previous one-shot quota path must remain callable, so persistent sessions
and scheduler behavior can be disabled or bypassed during troubleshooting.
