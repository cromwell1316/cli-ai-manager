# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 scripts/verify_install.sh
python3 scripts/verify_no_tui_surface.sh
python3 scripts/benchmark_runtime.py --scenario startup --iterations 20 --json
python3 profile_manager.py diagnostics --json
```

## Manual Validation

```bash
python3 profile_manager.py
python3 profile_manager.py list agy
python3 profile_manager.py status agy p1 --quota
python3 profile_manager.py audit status --json
python3 profile_manager.py service status --json
```

## Evidence Requirements

- Scenario matrix results.
- Failure drill results.
- Performance benchmark summaries.
- Install/update evidence.
- No-secret persistence evidence.
