# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "service"
python3 profile_manager.py service status --json
```

## Manual Validation

```bash
python3 profile_manager.py service start
python3 profile_manager.py list agy --json
python3 profile_manager.py service stop
```
