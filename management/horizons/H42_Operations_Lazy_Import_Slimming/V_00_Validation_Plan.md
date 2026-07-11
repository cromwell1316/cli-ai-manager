# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H42_Operations_Lazy_Import_Slimming/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
python3 -X importtime -c 'import profile_manager'
pytest -q tests/test_profile_manager.py -k "command or operations"
pytest -q tests/test_profile_manager.py -k "command or operations or import or export or sync or audit or service or config or quota or status or list"
python3 -m compileall -q cli_profile_manager
python3 scripts/benchmark_runtime.py --scenario all
```

## Evidence

- Import-time profile before and after implementation.
- Command smoke tests for affected operation paths.
- Cold startup and import benchmark medians.

## Results

```text
python3 -m pytest -q tests/test_profile_manager.py::test_operations_import_defers_command_specific_dependencies
1 passed in 3.05s

python3 -m pytest -q tests/test_profile_manager.py -k "command or operations"
17 passed, 173 deselected in 5.50s

python3 -m pytest -q tests/test_profile_manager.py -k "command or operations or import or export or sync or audit or service or config or quota or status or list"
140 passed, 50 deselected in 4.64s

python3 -m compileall -q cli_profile_manager
passed

python3 scripts/benchmark_runtime.py --scenario all
python-startup median=11.319ms
import-profile-manager median=31.770ms
parse-args median=5.414ms
command-config-json median=2.396ms
command-list-agy-json median=1.065ms
command-status-agy-json median=0.381ms
command-diagnostics-agy-json median=4.260ms
profile-index median=0.956ms
help median=40.806ms
list-agy-json median=54.047ms
diagnostics-agy-json median=99.392ms
config-json median=65.716ms
status-redraw median=0.014ms
quota-parser median=0.248ms
quota-cold-mock median=0.321ms
quota-warm-mock median=0.234ms
```
