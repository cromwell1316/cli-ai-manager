# V_01 Startup Benchmark Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- `python-startup` benchmark runs.
- `import-profile-manager` benchmark runs.
- `parse-args` benchmark runs.
- `command-execute` benchmark runs with fake profile roots.
- JSON output separates subprocess and in-process timings.

## Evidence

- `python3 scripts/benchmark_runtime.py --scenario python-startup --json`
  passed with median `29.547ms`.
- `python3 scripts/benchmark_runtime.py --scenario import-profile-manager --json`
  passed with median `37.501ms`.
- `python3 scripts/benchmark_runtime.py --scenario parse-args --json`
  passed with median `7.786ms`.
- `python3 scripts/benchmark_runtime.py --scenario command-execute --json`
  passed with fake profile roots and per-command results.
- Benchmark JSON now reports phase-specific result names and separates
  subprocess scenarios from in-process parser/handler scenarios.
