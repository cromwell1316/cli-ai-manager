# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H34_Log_Tail_And_Developer_Mode_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "developer or log or interactive"
python3 scripts/benchmark_runtime.py --scenario status-redraw
```

## Evidence

- Developer-mode redraw timing.
- Tail cache behavior for growing and truncated logs.
