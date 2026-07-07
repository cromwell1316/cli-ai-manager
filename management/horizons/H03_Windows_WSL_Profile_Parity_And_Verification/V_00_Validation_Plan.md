# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: validation plan

Status: implemented.

## Required Checks

```bash
python3 -m py_compile profile_manager.py
python3 profile_manager.py list agy --json
rg -n "oauth_creds.json|cred-p|gemini:antigravity|antigravity-oauth-token" profile_manager.py README.md
```

## Required Assertions

- Platform-specific credential models are documented and implemented.
- WSL status does not depend on Windows Credential Manager backups.
- Windows launch does not rely on `HOME` alone.
- Sync either converts credentials or refuses with a clear error.

## Failure Handling

If a fixture says a profile is active but the expected platform token file is
missing or invalid, status logic is wrong and must be fixed before proceeding.
