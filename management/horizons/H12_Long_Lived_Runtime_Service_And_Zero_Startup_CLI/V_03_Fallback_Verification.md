# V_03 Fallback Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Commands fall back to one-shot mode when the service is absent.
- Commands fall back to one-shot mode when the service times out.
- Service-backed JSON matches one-shot JSON for supported commands.

## Evidence

- `test_service_mode_falls_back_when_service_absent` verifies
  `AI_MAN_SERVICE=1` still executes one-shot when no socket is available.
- `test_service_backed_output_matches_one_shot` verifies service-backed
  `list agy --json` matches one-shot JSON output.
- Manual validation passed:
  - `python3 profile_manager.py service start --json`
  - `AI_MAN_SERVICE=1 python3 profile_manager.py list agy --json`
  - `python3 profile_manager.py service stop --json`
- Service failures return `None` to the client path, which then runs the normal
  parser and command handler.
