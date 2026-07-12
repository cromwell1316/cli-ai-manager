# H50 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Scope

Validate native Windows smoke coverage in CI.

## Checks

- Python syntax checks run on Windows.
- Focused Windows tests run without real tokens.
- `install-windows.ps1` works with temporary paths.
- Helper generation is verified.

## Commands

```powershell
python -m py_compile profile_manager.py cli_profile_manager\cli.py cli_profile_manager\operations.py
python -m pytest tests\test_profile_manager.py -k "windows"
.\install-windows.ps1 -BinDir $env:TEMP\ai-man-bin -AgyHome $env:TEMP\agy-homes -NoPathUpdate
```

```bash
python3 scripts/horizon_governance.py --json
```
