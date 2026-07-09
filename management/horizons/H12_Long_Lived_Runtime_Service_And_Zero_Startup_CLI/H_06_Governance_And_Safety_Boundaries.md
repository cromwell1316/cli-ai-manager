# H_06 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Service mode must remain optional.
- No TCP listener.
- No raw token persistence.
- No privileged installation requirement.
- No behavior drift between service-backed and one-shot output.
- Resource isolation from H13 should apply to child processes started by the
  service.
