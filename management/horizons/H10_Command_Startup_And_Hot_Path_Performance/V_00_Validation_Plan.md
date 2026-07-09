# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py scripts/*.py
python3 scripts/benchmark_runtime.py --scenario python-startup --json
python3 scripts/benchmark_runtime.py --scenario import-profile-manager --json
python3 scripts/benchmark_runtime.py --scenario parse-args --json
python3 scripts/benchmark_runtime.py --scenario command-execute --json
```

## Manual Profiling

```bash
python3 -X importtime profile_manager.py --help 2> /tmp/ai-man-importtime.log
python3 profile_manager.py --help
python3 profile_manager.py config show --json
```

## Evidence Requirements

- Record Python startup baseline separately from application import time.
- Record largest import-time modules before and after lazy-import changes.
- Record command handler budgets and actual in-process timings.
