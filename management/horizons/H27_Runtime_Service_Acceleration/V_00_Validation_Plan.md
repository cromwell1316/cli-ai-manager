# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H27_Runtime_Service_Acceleration/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

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

## Evidence

```bash
python3 -m py_compile cli_profile_manager/runtime_service.py cli_profile_manager/cli.py
pytest -q tests/test_profile_manager.py -k "runtime_service or service"
pytest -q tests/test_profile_manager.py -k "not test_in_process_command_perf_budgets"
```

Result: service/runtime `16 passed, 156 deselected`; broad suite `171 passed, 1 deselected`.

Manual socket validation confirmed health cache metrics after repeated
service-backed `list agy --json`: `entries=1`, `hits=1`, `misses=1`,
`snapshot_cached=true`, `snapshot_builds=1`.
