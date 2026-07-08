# H_04 Phase 04 Troubleshooting Docs

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Document the operational controls and common failure modes.

## Scope

- Document quota env vars, AGY columns, stale marker, failure marker, and retry
  behavior.
- Add examples for `quota`, `status --quota`, and diagnostics JSON.
- Add a section for local proxy usage during git/network operations if needed by
  the environment.

## Acceptance

- README tells users what `...`, `~`, and `!` mean.
- README explains how to tune AGY quota concurrency and timeout.
