# H45 Windows AGY Quota Backend

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make AGY quota probing work correctly on native Windows after the Windows/WSL
profile parity work. The quota path must use the same Credential Manager
switching model as `ai-man launch agy pN`.

## Goals

- Add a Windows-specific AGY quota backend that does not depend on Unix PTY
  support.
- Ensure the backend writes `cred-pN.json` into `gemini:antigravity` before
  probing.
- Preserve WSL/Linux quota behavior.
- Return clear `unsupported`, `missing_cli`, `auth_required`, timeout, and
  runtime failure states.
- Add tests for command construction, timeout handling, and no-token behavior.

## Non-Goals

- Do not change AGY credential formats.
- Do not implement a new Windows TUI.
- Do not weaken existing WSL quota tests.

## Work Areas

- Route native Windows AGY quota calls through the managed PowerShell helper.
- Decide whether the helper should expose a dedicated `Quota` action or reuse
  `Launch` with prompt arguments.
- Normalize quota diagnostics and JSON payloads across Windows and WSL.
- Document any AGY limitation caused by the shared Credential Manager slot.

## Validation

```bash
python3 -m py_compile profile_manager.py cli_profile_manager/cli.py cli_profile_manager/operations.py cli_profile_manager/quota.py
python3 -m pytest tests/test_profile_manager.py -k "quota or windows_agy"
python3 -m pytest
```

Acceptance target: `ai-man status agy pN --quota` and `ai-man quota agy pN`
return deterministic payloads on native Windows without importing Unix PTY-only
code paths.

## Files

- `README.md`
