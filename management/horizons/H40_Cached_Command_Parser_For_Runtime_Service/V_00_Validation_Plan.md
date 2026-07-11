# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: validation

Status: planned.

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
