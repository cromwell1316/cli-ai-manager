# V_01 IPC Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Socket path is user-owned and user-only.
- TCP listeners are not created.
- Invalid requests return stable JSON errors.
- Client timeouts are bounded.

## Evidence

- `test_runtime_service_paths_are_user_only` verifies runtime directory mode
  `0o700` under the metadata runtime area.
- `test_service_backed_output_matches_one_shot` starts the service and verifies
  socket mode `0o600`.
- The implementation uses `socket.AF_UNIX` and does not bind `AF_INET` or
  `AF_INET6`.
- Requests use newline-delimited JSON with protocol version checks and stable
  JSON error payloads for invalid actions or ineligible commands.
- Client requests use bounded socket timeouts and one-shot fallback.
