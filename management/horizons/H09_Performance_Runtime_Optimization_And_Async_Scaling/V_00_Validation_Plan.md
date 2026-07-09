# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py
./scripts/verify_no_tui_surface.sh
python3 profile_manager.py config show --json
python3 profile_manager.py diagnostics agy --json
python3 scripts/validate_agy_quota_live.py --dry-run --json
```

## Performance Validation

```bash
python3 scripts/benchmark_runtime.py --json
python3 scripts/benchmark_runtime.py --scenario status-redraw --profiles 12
python3 scripts/benchmark_runtime.py --scenario quota-parser --iterations 100
```

`scripts/benchmark_runtime.py` is implemented and can run command, status
redraw, and quota parser scenarios without real quota tokens.

## Manual Validation

```bash
python3 profile_manager.py list agy
python3 profile_manager.py list codex
python3 profile_manager.py list claude
```

Open interactive AGY status, observe first paint, auto-refresh countdown,
manual refresh behavior, stale white quota values, and keyboard responsiveness.
