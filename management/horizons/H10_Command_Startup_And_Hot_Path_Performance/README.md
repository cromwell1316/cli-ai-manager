# H10 Command Startup And Hot Path Performance

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Separate system Python startup cost from application overhead, then reduce
import, argument parsing, and command execution latency for common non-quota
commands.

## Goals

- Benchmark startup in separate phases: Python startup, app import,
  argument parsing, and command execution.
- Profile imports with `python3 -X importtime profile_manager.py --help`.
- Move heavy top-level imports out of the CLI entrypoint and into lazy command
  paths.
- Add in-process performance tests for command handlers so local regressions do
  not depend on subprocess startup noise.
- Optimize `--help`, `config show`, `list`, `status`, and `diagnostics` only
  after measurement identifies the hot path.

## Non-Goals

- Do not change command names, flags, JSON shapes, or exit codes.
- Do not optimize quota PTY probing in this horizon.
- Do not add a daemon or background service here; that belongs to H12 if still
  needed after entrypoint optimization.
- Do not hide slow measurements caused by the host Python runtime.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Startup_Benchmark_Decomposition.md`
- `H_02_Phase_02_Import_Profile_And_Lazy_Entrypoint.md`
- `H_03_Phase_03_In_Process_Command_Perf_Harness.md`
- `H_04_Phase_04_Command_Hot_Path_Optimization.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Startup_Benchmark_Verification.md`
- `V_02_Import_Profile_Verification.md`
- `V_03_Command_Perf_Verification.md`
- `V_04_Acceptance_Matrix.md`
