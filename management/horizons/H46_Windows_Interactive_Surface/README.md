# H46 Windows Interactive Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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

## Files

- `README.md`
