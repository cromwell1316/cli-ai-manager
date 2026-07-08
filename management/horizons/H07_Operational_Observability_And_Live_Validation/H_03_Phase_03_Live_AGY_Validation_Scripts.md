# H_03 Phase 03 Live AGY Validation Scripts

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Add repeatable live validation scripts for AGY quota behavior across real
profiles.

## Scope

- Add a script that probes configured AGY profiles with bounded concurrency.
- Emit sanitized timing, state, and quota-column summaries.
- Support a dry-run mode that checks profile/token discovery without launching
  native AGY.
- Keep live validation opt-in.

## Acceptance

- Script produces useful evidence for p1-p12 without storing secrets.
- Failures include state, elapsed time, and diagnostic warning.
