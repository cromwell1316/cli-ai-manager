# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py
./scripts/verify_no_tui_surface.sh
```

## Manual Validation

```bash
python3 profile_manager.py quota agy p1 --json --timeout 60
python3 profile_manager.py status agy p1 --json --quota --timeout 60
```

Open interactive `ai-man`, view AGY status, and verify:

- account/token rows appear immediately;
- retryable quota rows wake and retry without pressing Enter;
- stale values remain visible during failed refreshes;
- repeated failures do not permanently poison a persistent session.

## Evidence Collected

- `python3 -m pytest -q` passes.
- `python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py tests/test_profile_manager.py` passes.
- `./scripts/verify_no_tui_surface.sh` passes.
- Manual live AGY validation was not run in this environment.
