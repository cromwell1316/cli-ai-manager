# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
./scripts/verify_install.sh
./scripts/verify_no_tui_surface.sh
python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json
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

## Evidence Captured

- `python3 -m pytest -q`: 118 tests passed.
- `./scripts/verify_install.sh`: install verification passed.
- `./scripts/verify_no_tui_surface.sh`: TUI surface verification passed.
- `python3 scripts/benchmark_runtime.py --scenario all --iterations 20 --json`:
  completed successfully with status redraw median 0.466 ms and quota parser
  median 0.138 ms.
- `diagnostics --json`, `audit status --json`, and `service status --json`
  completed successfully with temporary roots.
- No test secrets were found in H22 JSON/error artifacts.
