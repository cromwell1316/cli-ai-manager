# H_01 Phase 01 Diagnostics Command

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Expose a noninteractive diagnostics command for safe runtime inspection.

## Scope

- Add `ai-man doctor` or `ai-man diagnostics`.
- Support `--json`.
- Report configured profile roots, visible profiles, CLI availability, quota
  scheduler state, cache entries, retry deadlines, and persistent session counts.
- Redact account identifiers unless explicitly requested with a safe flag.

## Acceptance

- Diagnostics runs without requiring valid tokens.
- JSON shape is stable and covered by tests.
- No token material is printed.
