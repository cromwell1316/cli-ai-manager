# H26 Startup And Import Slimming

Owner: cli-profile-manager
Source of Truth: management/horizons/H26_Startup_And_Import_Slimming/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Reduce cold command startup overhead for common direct commands. In-process
handlers are already fast; subprocess commands still pay Python startup, module
import, parser construction, and compatibility-layer costs.

## Goals

- Keep `--help`, `config show`, `list`, and `status` on minimal import paths.
- Move heavy imports behind command-specific boundaries.
- Reduce top-level compatibility wrappers in `cli.py`.
- Keep command names, flags, output, and exit codes unchanged.
- Track import-time regressions explicitly.

## Non-Goals

- Do not change profile layout or credential parsing.
- Do not optimize live quota probing in this horizon.
- Do not require the runtime service for basic commands.

## Work Areas

- Profile with `python3 -X importtime profile_manager.py --help`.
- Review top-level imports in `profile_manager.py`, `cli.py`, and `operations.py`.
- Split parser construction for common and heavy command groups.
- Remove duplicate indirection where it adds import cost without isolation value.
- Keep lazy imports covered by tests.

## Validation

```bash
python3 scripts/benchmark_runtime.py
pytest -q tests/test_profile_manager.py::test_help_and_config_show_do_not_import_quota_module
pytest -q tests/test_profile_manager.py::test_in_process_command_perf_budgets
```

Acceptance target: lower cold `help`, `config show --json`, and `list agy
--json` latency without regressing in-process command budgets.

## Implementation Evidence

- Removed the unconditional cold `reload(cli)` in `profile_manager.py`; repeated
  in-process compatibility reloads still refresh the CLI module.
- Skipped command audit initialization for parser help paths so `--help` avoids
  audit setup before `argparse` exits.
- Kept audit enabled for passthrough help arguments such as
  `launch agy p1 -- -h`.
- Benchmark after implementation:
  - `help` median: `44.380ms`
  - `list-agy-json` median: `90.501ms`
  - `diagnostics-agy-json` median: `143.070ms`
  - `config-json` median: `130.612ms`
- Targeted H26 tests passed:
  - `test_help_and_config_show_do_not_import_quota_module`
  - `test_parser_help_detection_ignores_launch_passthrough_help`
  - `test_in_process_command_perf_budgets`

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Import_Baseline.md`
- `H_02_Phase_02_Lazy_Surface_And_Parser_Slimming.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
