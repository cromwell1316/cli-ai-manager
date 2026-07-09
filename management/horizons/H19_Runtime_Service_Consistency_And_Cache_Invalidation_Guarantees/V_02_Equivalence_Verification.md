# V_02 Equivalence Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H19_Runtime_Service_Consistency_And_Cache_Invalidation_Guarantees/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Verification

- Service-backed read-only commands match one-shot commands.
- Exit codes and error shapes match.
- Fallback is transparent to eligible commands.
- Config values match between execution modes.
