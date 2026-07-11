# H31 Config Fast Path And Health Split

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Make `config show` cheap and deterministic by separating effective settings
from heavier health checks.

## Goals

- Keep effective config resolution fast.
- Move environment health, path existence, and runtime checks into explicit
  health/doctor paths.
- Reuse config registry parsing.
- Preserve current config JSON compatibility where practical.
- Keep warnings for invalid environment values.

## Non-Goals

- Do not remove existing env variable support.
- Do not change defaults.
- Do not make config depend on live CLI availability.

## Work Areas

- Separate pure config resolution from health inspection.
- Cache registry metadata.
- Avoid importing quota, interactive, or diagnostics from config show.
- Add a compatibility shim if existing JSON fields need gradual migration.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "config"
```

Acceptance target: reduce `config show --json` latency while keeping effective
settings and warnings correct.

## Implementation Notes

- `config show` now uses a fast, pure effective-config path.
- Process limit settings remain in `config show` for JSON compatibility, but
  live backend resolution is deferred there.
- `config health` provides the explicit health/deep path with live process
  backend resolution.
- Diagnostics continue to receive config health through the explicit health
  payload.
- Registry lookup metadata is cached for setting resolution.

## Evidence

```bash
python3 -m py_compile cli_profile_manager/config.py cli_profile_manager/process_policy.py cli_profile_manager/operations.py cli_profile_manager/cli.py
pytest -q tests/test_config_fast_path.py
pytest -q tests/test_profile_manager.py -k "config"
pytest -q tests/test_profile_manager.py tests/test_config_fast_path.py -k "not test_in_process_command_perf_budgets"
python3 scripts/benchmark_runtime.py --scenario commands
```

Results: H31 tests `4 passed`; existing config tests `6 passed, 170 deselected`;
broad suite `179 passed, 1 deselected`. In this run `config-json` median changed
from `129.546ms` before H31 to `93.310ms` after H31.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Config_Purity_Audit.md`
- `H_02_Phase_02_Fast_Config_And_Health_Command.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
