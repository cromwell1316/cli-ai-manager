# V_04 Phase 04 Launch Sync Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H03_Windows_WSL_Profile_Parity_And_Verification/README.md
Lifecycle: living
Document Class: phase verification

Status: implemented.

## Checks

```bash
python3 profile_manager.py sync --help
python3 profile_manager.py launch agy p1 --dry-run
python3 profile_manager.py sync --from wsl --mode soft --dry-run
python3 profile_manager.py sync --from windows --mode soft --dry-run
```

## Pass Criteria

- Windows dry-run launch shows Credential Manager switcher use.
- WSL dry-run launch shows isolated `HOME` only.
- Sync dry-run reports conversion actions.
- Hard sync dry-run reports deletions before requiring confirmation.
