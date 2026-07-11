# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "parser or command or runtime"
python3 scripts/benchmark_runtime.py --scenario parse-args
python3 scripts/benchmark_runtime.py --scenario command-execute
```

## Evidence

- Repeated parse tests.
- Command grammar equivalence tests.
- Parse and in-process command benchmark medians.

## Validation Results

```bash
pytest -q tests/test_runtime_parser_cache.py
# 5 passed

pytest -q tests/test_profile_manager.py -k "parser or command or runtime"
# 45 passed, 144 deselected

python3 scripts/benchmark_runtime.py --scenario parse-args
# parse-args median 31.275ms

python3 scripts/benchmark_runtime.py --scenario command-execute
# command-config-json median 12.952ms
# command-list-agy-json median 5.965ms
# command-status-agy-json median 1.135ms
# command-diagnostics-agy-json median 16.682ms
```
