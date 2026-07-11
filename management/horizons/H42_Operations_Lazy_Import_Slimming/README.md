# H42 Operations Lazy Import Slimming

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Reduce cold command startup cost by moving heavy operation dependencies out of
the import path for commands that do not need them.

## Goals

- Lower `import profile_manager` and cold simple-command time.
- Keep public operation behavior unchanged.
- Move only dependencies with clear measured startup impact.
- Avoid circular imports and hidden runtime side effects.

## Non-Goals

- Do not split modules without measured benefit.
- Do not change operation result structures.
- Do not delay imports that are already cheap or required by most commands.

## Work Areas

- Use import-time profiles to identify costly operation imports.
- Move selected imports into command-specific functions.
- Add smoke coverage for affected commands.
- Compare import and command benchmarks before and after.

## Validation

```bash
python3 -X importtime -c 'import profile_manager'
pytest -q tests/test_profile_manager.py -k "command or operations"
python3 scripts/benchmark_runtime.py --scenario all
```

Acceptance target: cold import/startup improves without changing command output
or test-visible behavior.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Import_Profile_Inventory.md`
- `H_02_Phase_02_Targeted_Lazy_Import_Migration.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
