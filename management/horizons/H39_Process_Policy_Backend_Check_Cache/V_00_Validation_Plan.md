# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H39_Process_Policy_Backend_Check_Cache/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "process or config or diagnostics"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

## Evidence

- Cache hit and invalidation tests.
- Fallback behavior tests for unavailable systemd.
- Config and diagnostics benchmark medians.

Completion evidence:

- `pytest -q tests/test_profile_manager.py -k "process or config or diagnostics"`
- `python3 scripts/benchmark_runtime.py --scenario command-execute`
