# H_04 Phase 04 CLI Client And Fallback

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make the normal CLI able to use the service when available while preserving
one-shot behavior.

## Scope

- Add an opt-in env var or config flag for service-backed command execution.
- Fall back to one-shot handlers on service errors.
- Keep JSON and text output identical.
- Add timeout and retry behavior for the local client.

## Acceptance

- Users can disable service mode instantly.
- Service failures do not prevent basic command use.
