# H35 Tmux Quota Session Pool Tuning

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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
pytest -q tests/test_profile_manager.py -k "tmux or quota"
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
tmux ls
```

Acceptance target: multi-profile AGY quota refreshes complete with bounded
session count and no orphaned manager-owned tmux sessions.
