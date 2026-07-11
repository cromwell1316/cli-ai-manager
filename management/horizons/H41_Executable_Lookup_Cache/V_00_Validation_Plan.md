# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or process or executable"
python3 scripts/benchmark_runtime.py --scenario all
```

## Evidence

- Lookup cache hit and miss tests.
- `PATH` invalidation tests.
- Startup, process policy, and quota benchmark medians.
