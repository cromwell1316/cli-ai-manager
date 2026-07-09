# H18 Configuration Surface Consolidation And Effective Settings UX

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make configuration discoverable, validated, source-aware, and safe to display.

## Goals

- Create a central config registry for defaults, environment overrides, metadata
  config, types, validation, and redaction.
- Expose effective settings with source information.
- Consolidate quota, runtime service, process policy, audit, and UI settings.
- Add validation for invalid values and unsafe combinations.
- Update diagnostics and docs from the same registry where practical.

## Non-Goals

- Do not require a global system config file.
- Do not expose secrets through config display.
- Do not break existing environment variables without migration aliases.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Config_Inventory_And_Registry.md`
- `H_02_Phase_02_Effective_Settings_Command_Surface.md`
- `H_03_Phase_03_Validation_Migration_And_Diagnostics.md`
- `H_04_Phase_04_Documentation_And_Compatibility.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Config_Registry_Verification.md`
- `V_02_Command_Surface_Verification.md`
- `V_03_Acceptance_Matrix.md`
