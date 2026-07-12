# H54 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate native Windows installation, profile conflict detection, cleanup
diagnostics, and rollback behavior.

## Commands

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
.\scripts\repair_windows_profile.ps1
ai-man diagnostics --json
```

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
```

## Evidence

- Installer chooses a working Python launcher.
- Verification reports PATH, helper, and profile conflicts clearly.
- Cleanup dry-run never mutates profile files without confirmation.
- Confirmed cleanup requires `-Apply -ConfirmCleanup` and writes profile backup
  files before commenting stale entries.
