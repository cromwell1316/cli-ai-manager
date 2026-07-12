# H46 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H46_Windows_Interactive_Surface/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Scope

Validate a native Windows interactive selector that avoids Unix terminal
dependencies.

## Checks

- `ai-man` with no arguments opens a usable Windows selector.
- Direct commands continue to work on Windows.
- WSL/Linux interactive behavior remains unchanged.
- Unix-only modules are not imported on native Windows startup.

## Commands

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/interactive.py
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows"
python3 -m pytest
```
