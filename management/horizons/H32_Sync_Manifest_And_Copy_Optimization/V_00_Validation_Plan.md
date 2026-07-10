# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "sync"
python3 profile_manager.py sync --from wsl --mode soft --dry-run
```

## Evidence

- Same sync result before/after.
- Faster dry-run on large fixtures.
