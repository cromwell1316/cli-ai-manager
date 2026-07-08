# H_02 Phase 02 Safe Debug Logging

Owner: cli-profile-manager
Source of Truth: management/horizons/H07_Operational_Observability_And_Live_Validation/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Make quota runtime decisions visible in logs without leaking secrets.

## Scope

- Log quota job enqueue/start/finish with tool, profile number, state, duration,
  and failure class.
- Log persistent session start/close/restart events.
- Redact emails by default or hash them consistently.
- Add a debug env flag for verbose quota diagnostics.

## Acceptance

- Tests prove token-like strings are not logged.
- Logs identify slow or failing profiles clearly enough for troubleshooting.
