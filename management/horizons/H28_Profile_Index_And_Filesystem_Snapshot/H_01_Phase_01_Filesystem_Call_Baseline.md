# H_01 Phase 01 Filesystem Call Baseline

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Measure repeated filesystem calls for list, status, diagnostics, and
interactive status rendering.

## Deliverables

- Filesystem call inventory.
- Profile root fixture for benchmarks.
- Hot call list.
- Index invalidation requirements.

## Result

The hot repeated calls were profile-root discovery, credential/account
existence checks, per-profile status construction, and service response reuse
after external profile file changes. These are now covered by command-scoped
profile indexes and service stale-fingerprint checks.
