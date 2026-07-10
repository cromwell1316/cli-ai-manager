# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H30_Interactive_Render_Loop_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario status-redraw
pytest -q tests/test_profile_manager.py -k "interactive or render"
```

## Evidence

- Redraw timing before/after.
- Screenshot/text fixture equivalence where applicable.
