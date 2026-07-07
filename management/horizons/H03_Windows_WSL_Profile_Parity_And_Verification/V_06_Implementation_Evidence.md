# V_06 Implementation Evidence

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: implementation evidence

Status: implemented.

## Evidence Log

- `profile_manager.py` now treats WSL agy OAuth as
  `.gemini/oauth_creds.json`.
- Windows agy backup files are `cred-pN.json` with
  `Target: gemini:antigravity` and `BlobBase64` containing OAuth JSON.
- Agy status reports `has_token: true` only when the authoritative platform
  credential parses; invalid JSON is surfaced as `token_state: invalid`.
- `ai-man import agy <cred-pN.json> pN` decodes Windows backup JSON and writes
  WSL `.gemini/oauth_creds.json` atomically.
- `ai-man export agy pN --to <path>` wraps WSL OAuth JSON into the Windows
  backup JSON shape atomically.
- Noninteractive sync converts agy credentials in both directions:
  WSL -> Windows refreshes `cred-pN.json`; Windows -> WSL refreshes
  `.gemini/oauth_creds.json`.
- Windows-native agy launch/login uses `agy-multiaccount.ps1`/PowerShell before
  running `agy`; WSL launch/login only sets isolated `HOME`.
- Synthetic fixture validation used `/tmp/cli-profile-manager-h03-fixtures` and
  did not contain real tokens.
- Validation passed:
  - `python3 -m py_compile profile_manager.py`
  - `python3 profile_manager.py list agy --json`
  - `python3 profile_manager.py import agy /tmp/cli-profile-manager-h03-fixtures/win/agy-homes/cred-p1.json p1`
  - `python3 profile_manager.py export agy p1 --to /tmp/cli-profile-manager-h03-fixtures/exported/cred-p1.json`
  - `python3 profile_manager.py sync --from wsl --mode soft --dry-run`
  - `python3 profile_manager.py sync --from windows --mode soft --dry-run`
  - `rg -n "oauth_creds.json|cred-p|gemini:antigravity|antigravity-oauth-token" profile_manager.py README.md`

## Residuals

- True simultaneous Windows agy isolation remains a residual while the
  `gemini:antigravity` Credential Manager slot is shared.
- Live mutation of the Windows Credential Manager slot remains outside dry-run
  validation and requires explicit user-run integration testing.
