# H04 Testable Core Sync Safety And Modularization

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Turn the current direct-command implementation into a safer and more testable
core before adding new user-facing features. The highest-risk areas are
credential correctness, sync deletion behavior, and Windows agy credential
boundaries.

## Goals

- Add focused pytest coverage for H02/H03 behavior using temporary profile homes.
- Make sync machine-readable and auditable before it mutates destination homes.
- Expand status diagnostics from a coarse token flag to a credential-state model.
- Make import, export, sync, and launch dry-run usable from scripts through JSON.
- Split credential conversion and sync logic out of `profile_manager.py` after
  the tests protect existing behavior.

## Non-Goals

- Do not add new product features such as tags, search, backup/restore, or shell
  completions in this horizon.
- Do not mutate the live Windows Credential Manager `gemini:antigravity` slot
  from dry-run, sync, import, or export flows.
- Do not perform a large CLI rewrite before the test layer exists.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Test_Layer.md`
- `H_02_Phase_02_Credential_Modules.md`
- `H_03_Phase_03_Sync_Safety_And_JSON.md`
- `H_04_Phase_04_Status_Diagnostics.md`
- `H_05_Phase_05_Modularization.md`
- `H_06_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Test_Layer_Verification.md`
- `V_02_Sync_Safety_Verification.md`
- `V_03_JSON_Contract_Verification.md`
- `V_04_Modularization_Verification.md`
- `V_05_Acceptance_Matrix.md`

## Related Assets

- `profile_manager.py`
- `tests/test_profile_manager.py`
- `management/horizons/H02_Keyboard_First_Profile_Command_Surface`
- `management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification`
