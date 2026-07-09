# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H12_Long_Lived_Runtime_Service_And_Zero_Startup_CLI/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 profile_manager.py service status --json
python3 profile_manager.py diagnostics --json
```

## Manual Validation

```bash
python3 profile_manager.py service start
python3 profile_manager.py list agy --json
python3 profile_manager.py service stop
```

## Evidence Requirements

- One-shot and service-backed output equivalence.
- Local socket permission evidence.
- Fallback behavior evidence.
