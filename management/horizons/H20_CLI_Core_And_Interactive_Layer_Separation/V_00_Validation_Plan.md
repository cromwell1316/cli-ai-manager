# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/verify_no_tui_surface.sh
python3 scripts/benchmark_runtime.py --scenario startup --iterations 10 --json
```

## Evidence Requirements

- Import boundary evidence.
- Operation unit tests.
- CLI compatibility tests.
- Interactive migration tests.
