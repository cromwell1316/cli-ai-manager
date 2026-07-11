# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "sync"
python3 profile_manager.py sync --from wsl --mode soft --dry-run
```

## Evidence

- Same sync result before/after.
- Faster dry-run on large fixtures.

## Recorded Results

```text
pytest -q tests/test_profile_manager.py -k "sync"
6 passed, 172 deselected in 0.24s
```

```text
AI_MAN_WSL_HOME=/tmp/h32-sync-validation/wsl AI_MAN_WINDOWS_HOME=/tmp/h32-sync-validation/windows python3 profile_manager.py sync --from wsl --mode soft --dry-run --json
returncode=0
```
