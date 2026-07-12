# H_02 Phase 02 AGY Conversion And Metadata Parity

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

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

## Completion Evidence

- WSL `.gemini/oauth_creds.json` converts to Windows `cred-pN.json` with the
  active account from `google_accounts.json`.
- Windows `cred-pN.json` converts to WSL `.gemini/oauth_creds.json` and writes
  `google_accounts.json` when the backup includes account metadata.
- Invalid Windows credential backups are reported in `conversion_items` with
  `status: invalid` and do not create destination profile files.
- Sync tests use only file backups and never call the native Windows Credential
  Manager helper.
