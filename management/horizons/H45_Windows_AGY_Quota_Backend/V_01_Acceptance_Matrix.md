# H45 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H45_Windows_AGY_Quota_Backend/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
|------|------------|
| Windows backend | AGY quota probes on native Windows do not enter Unix PTY code paths. |
| Credential switching | The selected `cred-pN.json` is applied before probing. |
| Errors | Missing CLI, missing token, timeout, and auth failures are distinct. |
| Regression | Existing WSL/Linux quota tests continue to pass. |
