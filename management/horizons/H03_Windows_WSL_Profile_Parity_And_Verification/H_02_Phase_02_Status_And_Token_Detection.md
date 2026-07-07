# H_02 Phase 02 Status And Token Detection

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Fix false `No Token` and false `Active` reports.

## Required Behavior

- WSL agy `has_token` is true when `.gemini/oauth_creds.json` exists and parses.
- Windows agy `has_token` is true when `cred-pN.json` exists and parses.
- Codex and Claude still check their configured credential files.
- Email/account display uses `google_accounts.json` when present, otherwise a
  safe `logged in` placeholder.
- Invalid JSON is reported as invalid token, not active.

## Phase Exit

Status output correctly reflects real fixture files across all tools.
