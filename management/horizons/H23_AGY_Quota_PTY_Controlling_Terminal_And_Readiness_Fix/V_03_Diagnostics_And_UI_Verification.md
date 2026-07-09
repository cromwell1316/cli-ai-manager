# V_03 Diagnostics And UI Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Diagnostics report specific AGY quota failure reasons.
- Audit records startup, readiness, command delivery, completion, and classified
  failure events.
- Stale values remain visible during retryable failures.
- Interactive `!` markers have corresponding diagnostics.
- Redaction tests prove no raw tokens or unredacted accounts are persisted.
