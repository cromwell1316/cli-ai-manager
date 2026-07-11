# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H44_Performance_Baseline_Refresh_And_Budget_Tightening/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
pytest -q tests/test_benchmark_guardrails.py
pytest -q
```

## Evidence

- Full benchmark JSON output.
- Budget threshold diff and rationale.
- Guardrail test result.
