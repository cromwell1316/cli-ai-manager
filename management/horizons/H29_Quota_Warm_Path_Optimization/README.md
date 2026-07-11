# H29 Quota Warm Path Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Reduce latency and resource use after quota sessions are already warm. The AGY
tmux backend fixed correctness; the next step is making repeated `/usage`
snapshots cheaper.

## Goals

- Measure cold startup separately from warm snapshot latency.
- Avoid unnecessary liveness checks and full-pane captures.
- Stop waiting fixed post-command sleeps when quota output is already visible.
- Keep parser correctness and recovery behavior.
- Keep Codex and Claude quota behavior stable.

## Non-Goals

- Do not remove the tmux backend.
- Do not hide stale quota values when refresh fails.
- Do not reduce safety by killing sessions aggressively.

## Work Areas

- Add warm quota timing metrics.
- Cache recent tmux liveness checks for a short interval.
- Poll capture output until quota markers appear instead of sleeping blindly.
- Capture smaller panes on success and larger panes on parser miss.
- Preserve parser miss invalidation threshold.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or tmux"
python3 scripts/validate_agy_quota_live.py --dry-run
```

Acceptance target: lower warm AGY quota refresh time with no increase in
`parser_miss`, `timeout`, or false `auth_required` states.

## Implementation Notes

- Tmux-backed AGY quota sessions now cache recent liveness checks for a short,
  configurable interval.
- Warm `/usage` snapshots poll short pane captures until quota output is parsed
  instead of sleeping for a fixed post-command delay.
- Parser misses fall back to a longer pane capture before returning, preserving
  diagnostic context and the existing parser-miss invalidation threshold.
- Persistent session snapshots expose warm-path metrics: latency, capture kind,
  capture count, bytes, and marker readiness.
- PTY behavior and quota payload shape remain unchanged.

## Evidence

```bash
python3 -m py_compile cli_profile_manager/quota.py
pytest -q tests/test_quota_warm_path.py
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py -k "quota or tmux"
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py -k "not test_in_process_command_perf_budgets"
python3 scripts/benchmark_runtime.py --scenario quota-parser
python3 scripts/validate_agy_quota_live.py --dry-run
```

Results: H29 tests `4 passed`; quota/tmux suite `85 passed, 93 deselected`;
broad suite `177 passed, 1 deselected`; quota parser benchmark median
`0.230ms`, p95 `0.307ms`.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Cold_Warm_Quota_Baseline.md`
- `H_02_Phase_02_Adaptive_Capture_And_Waiting.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
