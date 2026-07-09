# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Destructive operations require explicit confirmation.
- Dry-run must not mutate state.
- Prompt text must name the target and consequence.
- Safety logs and audit records must be redacted.
- New mutating commands must declare a policy before implementation.
