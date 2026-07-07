# H_01 Phase 01 Credential Model Authority

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Scope

Codify the per-platform agy credential model.

## Model

- Windows:
  - file profile: `%USERPROFILE%\agy-homes\pN\.gemini`
  - saved token backup: `%USERPROFILE%\agy-homes\cred-pN.json`
  - live account slot: Windows Credential Manager `gemini:antigravity`
  - launch path: `Set-AgyCred N`, set `USERPROFILE/HOME`, run `agy`
- WSL:
  - file profile: `$HOME/agy-homes/pN/.gemini`
  - live OAuth file: `$HOME/agy-homes/pN/.gemini/oauth_creds.json`
  - launch path: set `HOME`, run `agy`

## Phase Exit

Code and docs name one source of truth for each platform and do not use
`antigravity-oauth-token` as the WSL login detector unless separately proven.
