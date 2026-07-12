# H_03 Phase 03 Diagnostics And Regression Coverage

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Harden diagnostics, tests, and docs around Windows AGY quota behavior.

## Deliverables

- JSON diagnostics for Windows quota backend availability.
- Tests for missing PowerShell, missing AGY CLI, timeout, and invalid backup.
- README updates for Windows quota support and limitations.
- Regression proof that Linux/WSL quota paths still pass.

## Validation Focus

- `quota` and `status --quota` report stable states.
- Diagnostics are actionable and token-safe.
- Existing quota tests remain green.
