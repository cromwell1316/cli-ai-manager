# H_04 Phase 04 Diagnostics Audit And Test Harness

Owner: cli-profile-manager
Source of Truth: management/horizons/H17_Quota_Pipeline_Reliability_And_State_Machine_Hardening/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make quota behavior inspectable and prove reliability through deterministic
tests.

## Scope

- Add diagnostics for state machine, queue, cache, sessions, retries, and last
  failure.
- Emit H14 audit events for lifecycle transitions.
- Add fake native CLI and fake PTY harnesses.
- Add tests for concurrency, parser miss, auth required, process exit, timeout,
  stale refresh, and forced refresh.

## Acceptance

- Diagnostics can explain why a quota value is pending or stale.
- Audit can reconstruct quota job lifecycle.
- Tests cover successful and failing native CLI behavior without live CLIs.
