# H47 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate post-install checks for native Windows.

## Checks

- Shims exist for `ai-man`, `profile-man`, and `pman`.
- User PATH includes the shim directory when PATH update is enabled.
- Python and PowerShell are discoverable.
- The AGY helper exists and can be generated.
- Credential Manager API access is checked without exposing tokens.

## Commands

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man --help
ai-man list agy
```

```bash
python3 scripts/horizon_governance.py --json
```

## Results

- Static tests verify the Windows verifier contract, Credential Manager safety
  target, and shim-name parity with `install-windows.ps1`.
- `python3 scripts/horizon_governance.py --json`: passed.
- `python3 -m pytest tests/test_profile_manager.py -k "install"`: passed.
- `python3 -m pytest`: passed.

Native Windows live execution of `.\scripts\verify_install_windows.ps1` is
documented for post-install validation and is not run in this Linux/WSL test
environment.
