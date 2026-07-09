# H_06 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Do not disable quota probing globally as the fix.
- Do not store raw PTY output, OAuth tokens, auth headers, or unredacted account
  identifiers.
- Do not require live AGY network access in CI or the default test suite.
- Do not weaken process resource policies.
- Any AGY-specific heuristic must be covered by a fake-CLI regression test.
- Any fallback that hides a failure must remain visible in diagnostics and audit.
