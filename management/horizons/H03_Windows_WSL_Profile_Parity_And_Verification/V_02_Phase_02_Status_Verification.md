# V_02 Phase 02 Status Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
python3 -m py_compile profile_manager.py
python3 profile_manager.py list agy --json
python3 profile_manager.py status agy p1
python3 profile_manager.py status codex p1
python3 profile_manager.py status claude p1
```

## Negative Fixtures

- Missing `oauth_creds.json` in WSL agy is `No Token`.
- Invalid `oauth_creds.json` in WSL agy is invalid, not active.
- Missing `cred-pN.json` on Windows agy is `No Token`.

## Pass Criteria

Status reflects the platform's authoritative token file.
