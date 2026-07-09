# H_01 Phase 01 State Model And Failure Taxonomy

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: implementation phase

Status: completed.

## Objective

Define explicit quota states, transitions, and failures.

## Scope

- Define states: `empty`, `queued`, `running`, `available`, `stale_refreshing`,
  `retry_wait`, `failed`, `auth_required`, and `disabled`.
- Define legal transitions and transition metadata.
- Define failures: timeout, parser miss, missing CLI, process exit, auth
  required, empty output, PTY failure, and exception.
- Define UI markers and diagnostics for every state.

## Acceptance

- Illegal transitions are detectable in tests.
- UI and JSON output map every state intentionally.
- Existing failure names remain compatible or have documented migration.
