# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "tmux or quota"
```

## Live Validation

```bash
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
tmux ls
```
