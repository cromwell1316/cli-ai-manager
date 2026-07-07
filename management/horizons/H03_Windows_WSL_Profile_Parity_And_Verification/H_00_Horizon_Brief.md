# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: horizon brief

Status: implemented.

## Problem

The current Python manager mixes Windows and WSL agy token assumptions. Windows
requires writing `cred-pN.json` into the single Credential Manager target
`gemini:antigravity` before launch. WSL isolates by `HOME` and uses
`.gemini/oauth_creds.json`. The manager currently points agy token status and
conversion at `.gemini/antigravity-cli/antigravity-oauth-token`, which conflicts
with the WSL helper scripts and can produce false status.

## Desired Outcome

Credential source of truth is explicit per platform. Status, import, export,
launch, and sync all use the correct model and are verified by fixtures that do
not expose real secrets.

## Success Criteria

- WSL agy status detects `.gemini/oauth_creds.json`.
- Windows agy status detects `cred-pN.json` and uses the PowerShell switcher for
  launch/login.
- Windows backup JSON imports into WSL OAuth JSON format.
- WSL OAuth JSON exports into Windows backup JSON format.
- Sync performs the required conversion in both directions or refuses with a
  clear message.
