# H20 CLI Core And Interactive Layer Separation

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Separate business operations from CLI parsing and interactive presentation so
behavior can be reused, tested, audited, and rendered consistently.

## Goals

- Create operation-level APIs for profile, credential, sync, quota, service,
  config, and audit actions.
- Keep CLI parsing thin and move behavior into testable core modules.
- Keep interactive screens as presentation and workflow orchestration only.
- Standardize operation result envelopes.
- Reduce broad imports between `interactive.py` and `cli.py`.

## Non-Goals

- Do not rewrite the application architecture from scratch.
- Do not change public command names as part of this horizon.
- Do not remove compatibility exports without a migration plan.

## Implementation Summary

- Added `cli_profile_manager.operations` as the core operation layer.
- Moved profile status, list/status/quota payloads, credential import/export,
  label, clear, sync, config, audit, runtime service, and launch preparation
  behavior behind operation APIs.
- Kept CLI command handlers as parsing/formatting/policy wrappers.
- Migrated interactive imports away from broad CLI business helpers toward
  operation APIs while preserving color constants and CLI launch handoff.
- Added operation result envelopes for success, validation error, not found, no
  token, runtime failure, and cancellation.
- Preserved lazy quota imports for `--help` and `config show` hot paths.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Boundary_Audit_And_Operation_Model.md`
- `H_02_Phase_02_Core_Service_Extraction.md`
- `H_03_Phase_03_CLI_And_Interactive_Migration.md`
- `H_04_Phase_04_Testing_Compatibility_And_Cleanup.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Boundary_Verification.md`
- `V_02_Migration_Verification.md`
- `V_03_Acceptance_Matrix.md`
