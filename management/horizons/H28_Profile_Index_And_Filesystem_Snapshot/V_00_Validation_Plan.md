# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H28_Profile_Index_And_Filesystem_Snapshot/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "snapshot or status or diagnostics"
python3 scripts/benchmark_runtime.py --scenario command-execute
```

## Evidence

- Reduced repeated filesystem calls.
- Equal status payloads.

## Recorded Results

```text
pytest -q tests/test_profile_manager.py -k "snapshot or status or diagnostics"
31 passed, 143 deselected in 1.48s
```

```text
python3 scripts/benchmark_runtime.py --scenario command-execute
command-config-json     median= 52.019ms
command-list-agy-json   median=  7.443ms
command-status-agy-json median=  6.969ms
command-diagnostics-agy-json median= 43.780ms
```
