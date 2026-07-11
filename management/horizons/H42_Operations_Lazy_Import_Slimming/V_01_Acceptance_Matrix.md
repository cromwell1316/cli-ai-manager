# V_01 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: validation

Status: completed.

| Area | Acceptance | Evidence |
| --- | --- | --- |
| Measurement | Moved imports have measured startup cost | H_01 inventory and `python3 -X importtime` profiles |
| Behavior | Operation outputs and command behavior are unchanged | `tests/test_profile_manager.py -k "command or operations"` and broader operation smoke |
| Startup | Cold import or simple command medians improve | `python3 scripts/benchmark_runtime.py --scenario all` |
| Lazy boundary | Command-specific modules are deferred after plain `operations` import | `test_operations_import_defers_command_specific_dependencies` |
| Risk control | Deferred imports and intentionally top-level imports are documented | H_01 and H_02 notes |
