# H47 Windows Install Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Add first-class verification for native Windows installation so users can prove
that shims, PATH, Python, AGY helper generation, and Credential Manager access
are ready after `install-windows.ps1`.

## Goals

- Add `scripts/verify_install_windows.ps1`.
- Verify `ai-man`, `profile-man`, and `pman` shims in the configured bin
  directory.
- Verify user PATH contains the shim directory unless explicitly skipped.
- Verify the managed AGY helper exists and can load.
- Verify Credential Manager API access with a safe non-mutating or reversible
  check.
- Keep the existing WSL/Linux verification script unchanged.

## Non-Goals

- Do not require valid AGY account credentials for install verification.
- Do not mutate real profile tokens except in a clearly reversible test mode.
- Do not install Python automatically.

## Work Areas

- Implement PowerShell verification script.
- Add README instructions for verification and rollback on Windows.
- Add tests or static checks for generated shim contents.
- Document common failures: missing Python, blocked execution policy, PATH not
  refreshed, and missing PowerShell.

## Validation

```powershell
.\install-windows.ps1
.\scripts\verify_install_windows.ps1
ai-man --help
ai-man list agy
```

Acceptance target: Windows users have a deterministic post-install command that
reports actionable failures without exposing tokens.

## Files

- `README.md`
