# V_05 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

| Requirement | Status |
| --- | --- |
| Status screen wakes on retry deadlines | Implemented |
| Idle status screen still blocks for input | Implemented |
| Timeout invalidates persistent PTY session | Implemented |
| Process exit invalidates persistent PTY session | Implemented |
| Other profile sessions remain isolated | Implemented |
| Empty output classified separately | Implemented |
| Parser miss classified separately | Implemented |
| Auth and missing CLI diagnostics preserved | Implemented |
| Stale successful quota survives failed refresh | Implemented |
| Deterministic automated runtime tests | Implemented |
