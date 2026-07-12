# H_01 Phase 01 Scenario Matrix And Fixtures

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Define the cross-platform sync scenario matrix.

## Deliverables

- Fixtures for WSL roots and Windows roots.
- AGY, Codex, Claude, and metadata coverage.
- Cases for soft sync, hard sync, dry-run, and explicit root overrides.

## Validation Focus

- Fixtures contain no real tokens.
- Scenario names map directly to expected sync output.

## Completion Evidence

- `test_cross_platform_sync_e2e_wsl_to_windows_preserves_all_managed_roots`
  builds synthetic WSL and Windows roots with AGY, Codex, Claude, and metadata.
- `test_cross_platform_sync_e2e_windows_to_wsl_hard_mode_and_invalid_reporting`
  covers hard-mode delete planning, invalid AGY backup reporting, and metadata
  preservation.
- `test_sync_cli_json_reports_explicit_root_overrides` validates explicit
  `AI_MAN_WSL_HOME` and `AI_MAN_WINDOWS_HOME` root overrides in CLI JSON.
