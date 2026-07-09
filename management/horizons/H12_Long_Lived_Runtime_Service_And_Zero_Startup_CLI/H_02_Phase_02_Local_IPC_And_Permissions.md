# H_02 Phase 02 Local IPC And Permissions

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Add a local-only IPC channel with safe filesystem permissions.

## Scope

- Prefer Unix domain sockets on Linux/WSL.
- Store runtime files under the existing user config/runtime area.
- Ensure socket and state files are user-only.
- Reject requests from unexpected users where the platform exposes credentials.
- Use a small JSON request/response protocol with stable errors.

## Acceptance

- IPC tests prove permission setup and request validation.
- The service never binds a TCP port.
