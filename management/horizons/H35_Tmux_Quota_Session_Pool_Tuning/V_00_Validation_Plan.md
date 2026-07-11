# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H35_Tmux_Quota_Session_Pool_Tuning/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
python3 -m py_compile cli_profile_manager/quota.py
pytest -q tests/test_tmux_pool_tuning.py
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py tests/test_tmux_pool_tuning.py -k "tmux or quota"
```

## Live Validation

```bash
python3 scripts/validate_agy_quota_live.py --concurrency 2 --timeout 60
tmux ls
```

Live validation remains an operator-run check because it can consume real AGY
quota and depends on local authenticated profiles.

## Recorded Results

```text
python3 -m py_compile cli_profile_manager/quota.py
```

```text
pytest -q tests/test_tmux_pool_tuning.py
5 passed in 0.09s
```

```text
pytest -q tests/test_profile_manager.py -k "tmux or quota"
81 passed, 100 deselected in 2.25s
```

```text
pytest -q tests/test_profile_manager.py tests/test_quota_warm_path.py tests/test_tmux_pool_tuning.py -k "tmux or quota"
90 passed, 100 deselected in 2.45s
```

```text
pytest -q
198 passed in 9.33s
```
