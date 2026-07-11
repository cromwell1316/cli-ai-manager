# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H36_Command_Parser_And_Dispatch_Simplification/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 scripts/benchmark_runtime.py --scenario parse-args
python3 scripts/benchmark_runtime.py --scenario command-execute
pytest -q tests/test_profile_manager.py -k "command or parser or cli"
```

## Evidence

- Command equivalence matrix.
- Parse and dispatch timing.

## Recorded Results

```text
python3 -m py_compile cli_profile_manager/cli.py tests/test_profile_manager.py
```

```text
pytest -q tests/test_profile_manager.py -k "command or parser or cli"
34 passed, 149 deselected in 2.23s
```

```text
python3 scripts/benchmark_runtime.py --scenario parse-args
parse-args median=8.641ms
```

```text
python3 scripts/benchmark_runtime.py --scenario command-execute
command-config-json median=8.719ms
command-list-agy-json median=6.931ms
command-status-agy-json median=7.781ms
command-diagnostics-agy-json median=44.793ms
```

```text
pytest -q
200 passed in 7.67s
```
