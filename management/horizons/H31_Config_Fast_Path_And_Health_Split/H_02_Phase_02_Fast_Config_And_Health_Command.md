# H_02 Phase 02 Fast Config And Health Command

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Separate fast effective config from heavier health inspection.

## Deliverables

- Fast config payload.
- Health/deep payload path.
- Registry metadata cache.
- Tests for invalid env warnings.

## Result

- `config show` uses fast `effective_config_payload(..., include_health=False)`.
- `config health` uses the explicit health path and resolves live process
  backends.
- Config diagnostics use the same explicit health payload.
- Tests cover invalid env warnings, redaction, deferred fast backend, and live
  health backend resolution.
