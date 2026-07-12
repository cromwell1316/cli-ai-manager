# H46 Windows Interactive Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Provide a native Windows interactive surface for `ai-man` without relying on
Unix terminal modules such as `termios`, `tty`, and `select`.

## Goals

- Replace the current native Windows direct-command fallback with a functional
  interactive selector.
- Keep the existing WSL/Linux interactive selector behavior unchanged.
- Support keyboard navigation, launch, login, import, export, sync, and
  settings workflows on Windows.
- Avoid importing Unix-only modules on native Windows.
- Add tests that prove `ai-man` with no arguments works on native Windows.

## Non-Goals

- Do not rewrite the WSL/Linux renderer unless required for shared boundaries.
- Do not change profile credential semantics.
- Do not add GUI dependencies.

## Work Areas

- Choose a Windows terminal input backend, such as `msvcrt` or a small
  cross-platform abstraction.
- Split interactive terminal dependencies behind platform-specific adapters.
- Add graceful degradation for terminals that do not support advanced keys.
- Update documentation with Windows interactive support notes.

## Validation

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/interactive.py
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows"
python3 -m pytest
```

Acceptance target: running `ai-man` with no arguments on native Windows opens a
usable selector instead of falling back to direct-command help.

## Completion Notes

- Added `cli_profile_manager/windows_interactive.py`, a native Windows console
  selector that avoids `termios`, `tty`, and Unix-only `select` usage.
- `cli.main()` now routes native Windows no-argument startup to the Windows
  selector instead of printing direct-command fallback help.
- The Windows selector supports launch, login/add, import, export, label,
  clear, sync, and settings workflows through the shared operations layer.
- WSL/Linux continues to use the existing interactive renderer unchanged.
- Added tests proving native Windows startup calls the Windows selector without
  importing `cli_profile_manager.interactive`, and that a launch workflow
  reaches the shared launcher.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Terminal_Dependency_Audit.md`
- `H_02_Phase_02_Windows_Input_And_Rendering_Adapter.md`
- `H_03_Phase_03_Workflow_Parity_And_Docs.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
