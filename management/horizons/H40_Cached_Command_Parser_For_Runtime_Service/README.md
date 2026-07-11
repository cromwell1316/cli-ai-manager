# H40 Cached Command Parser For Runtime Service

Owner: cli-profile-manager
Source of Truth: management/horizons/H40_Cached_Command_Parser_For_Runtime_Service/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Avoid rebuilding the argparse command tree for every in-process runtime-service
request while preserving the public parser factory for CLI startup and tests.

## Goals

- Add a cached parser path for long-lived runtime-service command execution.
- Keep `build_parser()` available as a fresh parser factory.
- Preserve command grammar, help text, aliases, and exit codes.
- Add tests that prove cached parsing does not leak parsed state.

## Non-Goals

- Do not replace argparse with a custom parser.
- Do not change command names or arguments.
- Do not cache mutable command results.

## Work Areas

- Introduce a clear runtime-service parser accessor.
- Audit parser state mutation during `parse_args`.
- Add coverage for repeated cached parses across different commands.
- Re-measure runtime-service command scenarios.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "parser or command or runtime"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

Acceptance target: runtime-service command execution avoids parser rebuild cost
without changing command behavior.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Parser_State_Audit.md`
- `H_02_Phase_02_Runtime_Service_Parser_Cache.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
