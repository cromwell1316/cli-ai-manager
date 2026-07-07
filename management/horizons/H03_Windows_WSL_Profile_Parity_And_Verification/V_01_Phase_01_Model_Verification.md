# V_01 Phase 01 Model Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
rg -n "oauth_creds.json|cred-pN|gemini:antigravity|Credential Manager" README.md profile_manager.py management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification
rg -n "antigravity-oauth-token" profile_manager.py
```

## Pass Criteria

- Docs and code agree on Windows and WSL credential authority.
- Any `antigravity-oauth-token` use is limited to non-authoritative metadata or
  removed.
