# H50 Native Windows CI Smoke Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H50_Native_Windows_CI_Smoke_Matrix/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Add native Windows CI smoke coverage so Windows support does not regress while
most development continues from WSL/Linux.

## Goals

- Run a Windows job that executes syntax checks and focused tests.
- Verify `install-windows.ps1` creates shims and helper files in a temporary
  location.
- Verify no Unix-only modules are imported for direct Windows commands.
- Verify AGY helper command construction and Credential Manager helper source.
- Keep CI token-safe and independent of real AGY credentials.

## Non-Goals

- Do not require live AGY, Codex, or Claude accounts in CI.
- Do not run destructive Credential Manager operations against a developer
  machine.
- Do not replace local Windows manual validation.

## Work Areas

- Add GitHub Actions Windows workflow or extend the existing test matrix.
- Add PowerShell smoke tests for installer output.
- Add Python tests that use platform abstraction instead of monkeypatching
  global `os.name`.
- Document how to reproduce the Windows CI smoke locally.

## Validation

```powershell
python -m py_compile profile_manager.py cli_profile_manager\cli.py cli_profile_manager\operations.py
python -m pytest tests\test_profile_manager.py -k "windows"
.\install-windows.ps1 -BinDir $env:TEMP\ai-man-bin -AgyHome $env:TEMP\agy-homes -NoPathUpdate
```

Acceptance target: every pull request gets native Windows signal for installer
and command-surface regressions.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_CI_Scope_And_Secrets_Boundary.md`
- `H_02_Phase_02_Workflow_Implementation.md`
- `H_03_Phase_03_Local_Reproduction_And_Governance.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
