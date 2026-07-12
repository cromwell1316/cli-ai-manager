# H47 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H47_Windows_Install_Verification/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
|------|------------|
| Shims | All supported command shims resolve to the repository entrypoint. |
| PATH | Verification reports whether a new shell is needed. |
| Helper | The managed AGY helper is present and current. |
| Safety | Verification does not leak or destroy real credentials. |
