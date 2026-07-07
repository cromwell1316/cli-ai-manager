# V_03 Phase 03 Conversion Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
python3 profile_manager.py import agy tests/fixtures/agy/cred-p1.synthetic.json p1
python3 profile_manager.py export agy p1 --to /tmp/agy-export-test
python3 -m py_compile profile_manager.py
```

## Pass Criteria

- Windows backup JSON converts to WSL `oauth_creds.json`.
- WSL `oauth_creds.json` converts to Windows backup JSON.
- Failed conversion leaves no partial credential file.
- Fixture tokens are synthetic.
