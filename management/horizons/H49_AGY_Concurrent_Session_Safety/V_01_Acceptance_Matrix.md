# H49 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H49_AGY_Concurrent_Session_Safety/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance |
|------|------------|
| Evidence | Parallel session behavior is documented from reproducible drills. |
| Guardrails | Risky concurrent Windows AGY launches have clear warnings or policy. |
| Recovery | Users can restore the intended Credential Manager slot. |
| Honesty | Docs do not claim true parallel isolation unless verified. |

## Result

Accepted with a conservative policy: same-user native Windows AGY parallel
sessions are unsupported, guarded by a named mutex, and documented with recovery
commands. True parallel isolation is documented as requiring separate Windows
users.
