# H35 Tmux Quota Session Pool Tuning

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Tune tmux-backed AGY quota sessions so they are reliable under p1-pN refresh
bursts without wasting processes or leaving stale sessions.

## Goals

- Bound cold session creation concurrency.
- Reuse warm sessions safely.
- Avoid evicting sessions that are still starting.
- Improve session ownership diagnostics.
- Keep cleanup scoped to manager-owned sessions.

## Non-Goals

- Do not kill user tmux sessions.
- Do not make tmux mandatory when backend is forced to PTY.
- Do not change profile authentication state.

## Work Areas

- Add cold-start concurrency limits separate from warm snapshot concurrency.
- Track per-session startup, ready, snapshot, close, and evict timing.
- Tune TTL and max-session defaults from observed behavior.
- Add stale session detection after external tmux kills.
- Add live validation across p1-p11.

## Validation

```bash
python3 -m py_compile cli_profile_manager/quota.py
pytest -q tests/test_tmux_pool_tuning.py
pytest -q tests/test_profile_manager.py -k "tmux or quota"
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
tmux ls
```

Acceptance target: multi-profile AGY quota refreshes complete with bounded
session count and no orphaned manager-owned tmux sessions.

## Implementation Notes

- Added separate tmux cold-start and warm-snapshot concurrency controls.
- Added pool and per-session lifecycle metrics to quota session snapshots.
- Hardened tmux ownership checks so cleanup only targets manager-owned sessions.
- Kept starting sessions out of eviction while recording evict and close timing.
- Added tests for pool tuning, non-manager cleanup safety, external kill recovery,
  and snapshot diagnostics.

## Validation Results

- `python3 -m py_compile cli_profile_manager/quota.py`
- `pytest -q tests/test_tmux_pool_tuning.py`: `5 passed in 0.09s`
- `pytest -q tests/test_profile_manager.py -k "tmux or quota"`:
  `81 passed, 100 deselected in 2.25s`
- `pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py tests/test_tmux_pool_tuning.py -k "tmux or quota"`:
  `90 passed, 100 deselected in 2.45s`
- `pytest -q`: `198 passed in 9.33s`
- Live AGY validation is documented as operator-run because it can consume real
  quota and depends on local authenticated profiles.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Pool_Metrics_And_Limits.md`
- `H_02_Phase_02_Eviction_And_Ownership_Hardening.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
