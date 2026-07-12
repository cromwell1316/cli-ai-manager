# H_02 Phase 02 AGY Conversion And Metadata Parity

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: horizon-phase

Status: planned.

## Objective

Validate AGY conversion and metadata preservation in both directions.

## Deliverables

- Tests for Windows `cred-pN.json` to WSL OAuth conversion.
- Tests for WSL OAuth to Windows `cred-pN.json` conversion.
- Account metadata preservation checks.
- Invalid credential reporting.

## Validation Focus

- Live Credential Manager slot is not mutated.
- Conversion items are reported in JSON output.
