# H43 Config Show Payload Construction Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H43_Config_Show_Payload_Construction_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

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

## Implementation

- Replaced the internal `SettingDefinition` dataclass with a lightweight
  slots-based class, preserving attributes and registry behavior.
- Removed plain config show's top-level dependency on `process_policy`; fast
  process-limit payloads are now built locally with the same deferred schema,
  while `config health` still imports and uses live `process_policy` checks.
- Removed `pathlib` from config payload construction for ordinary string path
  values.
- Built settings, `settings_by_key`, public settings, and warnings in one pass
  for `effective_config_payload`.
- Added schema and import-boundary regression tests for `config show --json`.

## Validation

```bash
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "config"
python3 scripts/benchmark_runtime.py --scenario command-execute
python3 scripts/benchmark_runtime.py --scenario commands
```

Acceptance target: config JSON output remains stable while construction time is
lower in both in-process and cold command benchmarks.

## Validation Results

- `python3 -m pytest -q tests/test_config_fast_path.py tests/test_profile_manager.py -k "config"`:
  14 passed, 184 deselected.
- `python3 -m pytest -q`: 220 passed.
- `python3 -m compileall -q cli_profile_manager`: passed.
- `python3 scripts/benchmark_runtime.py --scenario all`: completed.
  Representative H42 -> H43 medians:
  `command-config-json` 2.396ms -> 2.031ms,
  `config-json` 65.716ms -> 47.122ms,
  `import-profile-manager` 31.770ms -> 29.648ms.

Note: the current benchmark script does not expose `cold-subprocess`; the
equivalent cold command surface is `--scenario commands`.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Config_Payload_Profile.md`
- `H_02_Phase_02_Schema_Preserving_Construction_Slimming.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
