# H29 Quota Warm Path Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H29_Quota_Warm_Path_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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
