# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- Quota probing must remain optional.
- Raw PTY output must not be persisted.
- Retries must be bounded.
- Worker threads must be daemonized or explicitly closed.
- UI must show stale values clearly.
