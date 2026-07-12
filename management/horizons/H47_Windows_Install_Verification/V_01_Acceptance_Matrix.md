# H47 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
|------|------------|
| Shims | All supported command shims resolve to the repository entrypoint. |
| PATH | Verification reports whether a new shell is needed. |
| Helper | The managed AGY helper is present and current. |
| Safety | Verification does not leak or destroy real credentials. |

## Evidence

- `scripts/verify_install_windows.ps1` checks all supported PowerShell/CMD
  shims in the configured bin directory.
- The verifier fails when user PATH is missing the bin directory and warns when
  the current shell has not refreshed PATH yet.
- Helper freshness is compared against `windows_agy_helper_source`.
- Credential Manager access uses a temporary `ai-man-install-verify-*` target
  and never references the real `gemini:antigravity` target.
