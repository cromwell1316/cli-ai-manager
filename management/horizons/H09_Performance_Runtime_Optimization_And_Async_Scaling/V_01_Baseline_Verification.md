# V_01 Baseline Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H09_Performance_Runtime_Optimization_And_Async_Scaling/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Baseline benchmark script runs without real tokens.
- Cold and warm startup/list/status timings are recorded.
- Filesystem call counts are measured for status/list/diagnostics.
- Parser throughput is measured on sanitized captured output.

## Evidence

- `scripts/benchmark_runtime.py` provides `commands`, `status-redraw`, and
  `quota-parser` scenarios with JSON output.
- `test_runtime_benchmark_quota_parser_outputs_json` verifies the benchmark
  entrypoint in CI-safe mode.
- Local H09 run: `python3 scripts/benchmark_runtime.py --scenario quota-parser
  --iterations 5 --json` returned `ok: true`.
- Local H09 run: `python3 scripts/benchmark_runtime.py --scenario
  status-redraw --iterations 3 --profiles 12 --json` returned `ok: true`.
