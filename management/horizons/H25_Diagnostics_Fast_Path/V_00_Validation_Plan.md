# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H25_Diagnostics_Fast_Path/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "diagnostics"
```

## Evidence

- Before/after diagnostics timing.
- JSON compatibility sample.
- Redaction sample.
