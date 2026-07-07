# H_03 Phase 03 Import Export Conversion

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase

Status: planned.

## Scope

Make credential conversion explicit and reversible where possible.

## Required Behavior

- Windows `cred-pN.json` import into WSL:
  - decode `BlobBase64`;
  - parse the token payload;
  - write `.gemini/oauth_creds.json`;
  - write `.gemini/google_accounts.json` when account email is available.
- WSL export to Windows:
  - read `.gemini/oauth_creds.json`;
  - wrap it into the expected Windows backup JSON shape;
  - include `Target: gemini:antigravity`;
  - write outside the repo by default.
- Conversion uses temporary files and atomic replace to avoid partial tokens.

## Phase Exit

Fixture conversion passes both directions without using real credentials.
