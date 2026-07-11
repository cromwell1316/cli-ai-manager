# H_02 Phase 02 Targeted Lazy Import Migration

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Move selected heavy imports behind command-specific execution paths.

## Deliverables

- Lazy imports for measured candidates.
- Smoke tests for affected commands.
- Import benchmark comparison.
- Notes for any imports deferred because of risk.

## Implementation Notes

- Keep public modules importable.
- Do not change result classes or payload schemas.
- Keep lazy imports close to the code that uses them.

## Implementation

- Added cached lazy accessors inside `cli_profile_manager.operations` for:
  `_audit`, `_process_policy`, `_runtime_service`, `_sync`, `_config`,
  `_agy_credentials`, `_claude_credentials`, `_codex_credentials`,
  `_credentials_common`, and `_shutil`.
- Rewired config, audit, service, sync, launch preparation, status,
  import/export, and clear helpers to call those accessors only on demand.
- Replaced `dataclass` DTO declarations with explicit lightweight classes using
  the same constructor arguments and attributes.
- Added `test_operations_import_defers_command_specific_dependencies` to lock
  the lazy import boundary in a clean subprocess.

## Deferred Changes

- `metadata` and `paths` remain top-level because most operation flows need
  them immediately and moving them would create more risk than measured benefit.
