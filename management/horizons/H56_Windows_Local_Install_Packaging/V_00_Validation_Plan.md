# H56 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate Windows-local installation and packaging so native Windows use does not
depend on WSL UNC paths.

## Commands

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man --help
.\install-windows.ps1 -Rollback
.\install-windows.ps1 -Uninstall
```

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
```

## Evidence

- Shims point to Windows-local application files.
- Update and rollback keep commands usable after project moves.
- Verification distinguishes development UNC installs from local installs.
- Smoke coverage validates temporary local app/bin installs without tokens.
