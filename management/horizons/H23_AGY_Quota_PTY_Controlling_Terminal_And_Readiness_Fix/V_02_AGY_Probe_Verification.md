# V_02 AGY Probe Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- AGY readiness detection waits for `CLI ready for user input` or equivalent
  prompt readiness.
- `/usage` is sent after readiness and captured as command output.
- Parseable AGY usage output produces quota limits.
- Early process churn is not mislabeled as startup failure when the session is
  still usable.
- Persistent sessions can be reused after a successful probe.
