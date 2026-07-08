# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- Diagnostics must never print OAuth refresh tokens, API keys, or full credential
  JSON.
- Live validation must be opt-in because it can launch native CLIs.
- Evidence committed to the repo must be sanitized.
- Debug logs must prefer profile numbers and failure classes over account names.
