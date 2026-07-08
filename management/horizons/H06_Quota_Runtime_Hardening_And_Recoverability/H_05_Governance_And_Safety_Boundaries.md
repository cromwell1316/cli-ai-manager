# H_05 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Boundaries

- No real token contents may be written to fixtures or horizon evidence.
- Raw terminal output must be sanitized before being stored in normal JSON
  diagnostics.
- Session invalidation must be profile-scoped unless explicitly clearing all
  sessions.
- Retry logic must not create unbounded process fan-out.
- Changes must preserve existing noninteractive exit codes.

## Required Validation

- `python3 -m pytest -q`
- `python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py`
- `./scripts/verify_no_tui_surface.sh`
