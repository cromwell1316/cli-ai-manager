# H_02 Phase 02 Eviction And Ownership Hardening

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Make tmux cleanup precise, observable, and resilient to external session death.

## Deliverables

- Ownership checks.
- Dead session recovery.
- TTL and max-count tuning.
- Tests for external `tmux kill-session`.

## Implementation

- Cleanup and liveness checks require manager-owned tmux session names.
- Eviction skips sessions still in startup and records evict metrics for removed
  sessions.
- External tmux death invalidates the pooled session through the existing
  `process_exit` recovery path.
- Tests cover non-manager session safety, startup eviction protection, external
  kill recovery, and diagnostics.
