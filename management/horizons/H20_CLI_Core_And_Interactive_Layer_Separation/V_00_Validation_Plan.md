# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m pytest -q
./scripts/verify_no_tui_surface.sh
python3 scripts/benchmark_runtime.py --scenario python-startup --iterations 10 --json
```

## Evidence Requirements

- Import boundary evidence.
- Operation unit tests.
- CLI compatibility tests.
- Interactive migration tests.

## Evidence Captured

```bash
python3 -m pytest
python3 -m py_compile cli_profile_manager/operations.py cli_profile_manager/cli.py cli_profile_manager/interactive.py cli_profile_manager/terminal_rendering.py
```

Results:

- `python3 -m pytest`: 116 tests passed.
- `./scripts/verify_no_tui_surface.sh`: TUI surface verification passed.
- `python3 scripts/benchmark_runtime.py --scenario python-startup --iterations 10 --json`:
  median startup 9.997 ms in the local run.
