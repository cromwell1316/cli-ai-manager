# H03 Windows WSL Profile Parity And Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make profile management correct across Windows and WSL after the UI surface is
simplified. Windows and WSL use different agy credential mechanics, so parity
must be explicit and verified.

## Goals

- Treat Windows agy as `HOME/USERPROFILE` plus Credential Manager slot swapping.
- Treat WSL agy as isolated `HOME` plus `.gemini/oauth_creds.json`.
- Convert credentials correctly in both directions.
- Prevent false `Active` / `No Token` status.
- Add focused validation for import, export, sync, and launch semantics.

## Non-Goals

- Do not promise truly parallel Windows agy sessions beyond the known shared-slot
  limitation.
- Do not store secrets in repo files.
- Do not modify real Credential Manager entries during dry-run validation.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Credential_Model_Authority.md`
- `H_02_Phase_02_Status_And_Token_Detection.md`
- `H_03_Phase_03_Import_Export_Conversion.md`
- `H_04_Phase_04_Launch_And_Sync_Parity.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Phase_01_Model_Verification.md`
- `V_02_Phase_02_Status_Verification.md`
- `V_03_Phase_03_Conversion_Verification.md`
- `V_04_Phase_04_Launch_Sync_Verification.md`
- `V_05_Acceptance_Matrix.md`
- `V_06_Implementation_Evidence.md`

## Related Assets

- `/mnt/c/Users/Oliver/agy-multiaccount-README.md`
- `/mnt/c/Users/Oliver/agy-homes/agy-multiaccount.ps1`
- `/mnt/c/Users/Oliver/agy-homes/agy-multiaccount.sh`
- `/mnt/c/Users/Oliver/agy-homes/agy-add.sh`
- `profile_manager.py`
