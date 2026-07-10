# H36 Command Parser And Dispatch Simplification

Owner: cli-profile-manager
Source of Truth: management/horizons/H36_Command_Parser_And_Dispatch_Simplification/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Simplify command parsing and dispatch to reduce hot-path overhead and make
future optimizations easier.

## Goals

- Keep command grammar and output stable.
- Reduce duplicated wrappers between `cli.py`, `operations.py`, and
  `profile_manager.py`.
- Dispatch common read-only commands with minimal indirection.
- Keep heavy operations behind lazy module boundaries.
- Preserve testability of operation results.

## Non-Goals

- Do not remove public command aliases.
- Do not change exit codes.
- Do not merge interactive UI logic into command handlers.

## Work Areas

- Map direct commands to operation handlers through a compact table.
- Keep argparse construction cheap for common commands.
- Move compatibility helpers out of the startup path where possible.
- Keep operation results structured for JSON and text output.
- Add tests for command equivalence before and after simplification.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario parse-args
python3 scripts/benchmark_runtime.py --scenario command-execute
pytest -q tests/test_profile_manager.py -k "command or parser or cli"
```

Acceptance target: simpler dispatch with equal behavior and lower parse/dispatch
overhead.
