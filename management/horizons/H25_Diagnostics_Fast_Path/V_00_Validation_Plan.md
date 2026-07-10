# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Validation Evidence

```bash
pytest -q tests/test_profile_manager.py -k "diagnostics or config_diagnostics or process_limits"
python3 scripts/benchmark_runtime.py --scenario commands --iterations 5
python3 -m py_compile cli_profile_manager/diagnostics.py cli_profile_manager/cli.py
```

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "diagnostics"
```

## Evidence

- Before/after diagnostics timing.
- JSON compatibility sample.
- Redaction sample.
