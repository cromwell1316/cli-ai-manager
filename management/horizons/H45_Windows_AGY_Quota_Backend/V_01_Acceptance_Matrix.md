# H45 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
|------|------------|
| Windows backend | AGY quota probes on native Windows do not enter Unix PTY code paths. |
| Credential switching | The selected `cred-pN.json` is applied before probing. |
| Errors | Missing CLI, missing token, timeout, and auth failures are distinct. |
| Diagnostics | Native Windows AGY resolves to `windows-helper` in diagnostics. |
| Regression | Existing WSL/Linux quota tests continue to pass. |

## Evidence

- `run_windows_agy_quota_snapshot()` helper-backed runner.
- `operations.quota_probe_runner()` native Windows AGY selection.
- Tests for helper argv, timeout, missing backup, diagnostics, and operations
  runner selection.
