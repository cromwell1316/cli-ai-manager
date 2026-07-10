# H_02 Phase 02 Eviction And Ownership Hardening

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Make tmux cleanup precise, observable, and resilient to external session death.

## Deliverables

- Ownership checks.
- Dead session recovery.
- TTL and max-count tuning.
- Tests for external `tmux kill-session`.
