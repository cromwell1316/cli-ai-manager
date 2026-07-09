# H16 Sensitive Operation Safety And Confirmation Policy

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Create one safety policy for operations that can delete data, move credentials,
launch external tools, overwrite profiles, or sync between environments.

## Goals

- Classify operations by risk and required confirmation.
- Add a reusable preflight/result model for mutating actions.
- Standardize `--dry-run`, `--yes`, cancellation, and failure behavior.
- Audit every safety decision through H14 events.
- Prevent silent destructive behavior.
- Make recovery guidance consistent across CLI and interactive modes.

## Non-Goals

- Do not remove existing supported operations.
- Do not require confirmations for read-only commands.
- Do not persist credential payloads in safety reports.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Risk_Model_And_Command_Inventory.md`
- `H_02_Phase_02_Preflight_And_Confirmation_API.md`
- `H_03_Phase_03_Command_Migration.md`
- `H_04_Phase_04_Recovery_Diagnostics_And_Audit.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Policy_Verification.md`
- `V_02_Command_Migration_Verification.md`
- `V_03_Acceptance_Matrix.md`
