# V_02 Runtime State Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Profile and metadata caches invalidate after mutations.
- Service memory stays bounded.
- Quota sessions close on service shutdown.
- No raw token data appears in state snapshots or diagnostics.

## Evidence

- `test_mutating_command_notifies_runtime_invalidation` verifies mutating
  commands notify the runtime invalidation hook after successful execution.
- Runtime state stores only counters, generation, process id, and uptime; it
  does not persist raw credential content.
- Service-backed command execution reuses the existing redacted command
  handlers and captures stdout/stderr without writing command payloads to disk.
- `python3 profile_manager.py diagnostics --json` includes `service_runtime`
  health and paths without token data.
- Service shutdown removes pid and socket files; quota and PTY lifecycle remains
  governed by existing runtime shutdown behavior.
