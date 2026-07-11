# H42 Operations Lazy Import Slimming

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

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

## Implementation

- Moved command-specific `operations` dependencies behind lazy accessors:
  `audit`, `process_policy`, `runtime_service`, `sync`, `config`, AGY/Codex/Claude
  credential modules, credential common helpers, and `shutil`.
- Replaced the `dataclasses` dependency in `operations` with lightweight local
  DTO classes preserving the same public class names and attributes.
- Kept `metadata` and `paths` as top-level imports because core profile
  operations use them on common paths and moving them would add circular-import
  and readability risk.
- Added a subprocess smoke test proving `operations` import defers
  command-specific modules until the relevant operation is executed.

## Validation

```bash
python3 -X importtime -c 'import profile_manager'
pytest -q tests/test_profile_manager.py -k "command or operations"
pytest -q tests/test_profile_manager.py -k "command or operations or import or export or sync or audit or service or config or quota or status or list"
python3 -m compileall -q cli_profile_manager
python3 scripts/benchmark_runtime.py --scenario all
```

Acceptance target: cold import/startup improves without changing command output
or test-visible behavior.

## Validation Results

- `python3 -m pytest -q tests/test_profile_manager.py::test_operations_import_defers_command_specific_dependencies`:
  1 passed.
- `python3 -m pytest -q tests/test_profile_manager.py -k "command or operations"`:
  17 passed, 173 deselected.
- `python3 -m pytest -q tests/test_profile_manager.py -k "command or operations or import or export or sync or audit or service or config or quota or status or list"`:
  140 passed, 50 deselected.
- `python3 -m compileall -q cli_profile_manager`: passed.
- `python3 scripts/benchmark_runtime.py --scenario all`: completed.
  Representative before/after medians from this horizon run:
  `list-agy-json` 81.384ms -> 54.047ms,
  `config-json` 75.148ms -> 65.716ms,
  `import-profile-manager` 31.374ms -> 31.770ms.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Import_Profile_Inventory.md`
- `H_02_Phase_02_Targeted_Lazy_Import_Migration.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
