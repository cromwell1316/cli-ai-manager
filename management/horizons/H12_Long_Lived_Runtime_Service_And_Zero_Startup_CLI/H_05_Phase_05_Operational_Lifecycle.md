# H_05 Phase 05 Operational Lifecycle

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Provide predictable service lifecycle operations.

## Scope

- Add commands or subcommands for service `start`, `stop`, `restart`, and
  `status`.
- Detect stale pid/socket files.
- Expose service health in diagnostics.
- Add controlled shutdown for quota scheduler and persistent PTY sessions.

## Acceptance

- Lifecycle commands are idempotent.
- Stale service files are cleaned safely.
