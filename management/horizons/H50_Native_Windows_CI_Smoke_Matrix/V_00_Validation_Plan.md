# H50 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate native Windows smoke coverage in CI.

## Checks

- Python syntax checks run on Windows.
- Focused Windows tests run without real tokens.
- `install-windows.ps1` works with temporary paths.
- Helper generation is verified.

## Commands

```powershell
python -m py_compile profile_manager.py cli_profile_manager\cli.py cli_profile_manager\operations.py cli_profile_manager\windows_support.py cli_profile_manager\diagnostics.py
python -m pytest tests\test_profile_manager.py -k "windows"
.\scripts\windows_ci_smoke.ps1 -BinDir $env:TEMP\ai-man-bin -AgyHome $env:TEMP\agy-homes
```

```bash
python3 -m pytest tests/test_profile_manager.py -k "windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Completion Evidence

Local Linux validation covers syntax, focused Windows regression tests, workflow
contract checks, governance, and the full test suite. The PowerShell smoke is
the exact native Windows reproduction path used by GitHub Actions.
