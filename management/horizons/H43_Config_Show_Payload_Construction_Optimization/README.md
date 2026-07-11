# H43 Config Show Payload Construction Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Reduce `config show --json` payload construction overhead without changing the
reported configuration schema.

## Goals

- Preserve exact JSON field names and values.
- Avoid redundant intermediate structures where they are measurable.
- Keep health construction separated from plain config output.
- Add regression tests for JSON payload shape.

## Non-Goals

- Do not remove fields from config output.
- Do not change default configuration values.
- Do not introduce a new config file format.

## Work Areas

- Profile `effective_config_payload` and config JSON serialization.
- Simplify repeated conversion and merge work where safe.
- Keep config health checks opt-in for health/deep diagnostics paths.
- Re-measure `config-json` and cold subprocess scenarios.

## Validation

```bash
pytest -q tests/test_config_fast_path.py
python3 scripts/benchmark_runtime.py --scenario command-execute
python3 scripts/benchmark_runtime.py --scenario cold-subprocess
```

Acceptance target: config JSON output remains stable while construction time is
lower in both in-process and cold command benchmarks.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Config_Payload_Profile.md`
- `H_02_Phase_02_Schema_Preserving_Construction_Slimming.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
