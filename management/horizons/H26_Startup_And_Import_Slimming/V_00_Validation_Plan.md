# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H26_Startup_And_Import_Slimming/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -X importtime profile_manager.py --help
python3 scripts/benchmark_runtime.py
pytest -q tests/test_profile_manager.py::test_help_and_config_show_do_not_import_quota_module
```

## Evidence

- Import profile before/after.
- Startup benchmark before/after.

## Recorded Results

After implementation:

```text
help                   median=  44.380ms
list-agy-json          median=  90.501ms
diagnostics-agy-json   median= 143.070ms
config-json            median= 130.612ms
```

Targeted tests:

```text
3 passed in 1.13s
```
