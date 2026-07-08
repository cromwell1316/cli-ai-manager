# V_02 Session Recovery Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Unit test for timeout-triggered persistent session closure.
- Unit test for fresh session creation after invalidation.
- Unit test proving another profile session is not closed.

## Evidence

- `pytest -q` passes with fake persistent-session coverage for timeout
  invalidation, fresh session creation after invalidation, dead-session
  replacement, parser-miss threshold invalidation, and profile isolation.
