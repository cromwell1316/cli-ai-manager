# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H41_Executable_Lookup_Cache/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Automated Validation

```bash
pytest -q tests/test_profile_manager.py -k "quota or process or executable"
pytest -q tests/test_executable_lookup_cache.py
pytest -q tests/test_quota_warm_path.py
python3 scripts/benchmark_runtime.py --scenario all
```

## Evidence

- Lookup cache hit and miss tests.
- `PATH` invalidation tests.
- Startup, process policy, and quota benchmark medians.

## Results

```text
python3 -m pytest -q tests/test_executable_lookup_cache.py
4 passed in 0.06s

python3 -m pytest -q tests/test_quota_warm_path.py
4 passed in 0.13s

python3 -m pytest -q tests/test_profile_manager.py -k "quota or process or executable"
91 passed, 98 deselected in 2.82s

python3 scripts/benchmark_runtime.py --scenario all
python-startup median=11.036ms
import-profile-manager median=33.794ms
parse-args median=5.802ms
command-config-json median=2.073ms
command-list-agy-json median=0.899ms
command-status-agy-json median=0.360ms
command-diagnostics-agy-json median=3.986ms
profile-index median=0.877ms
help median=37.452ms
list-agy-json median=83.013ms
diagnostics-agy-json median=94.916ms
config-json median=71.320ms
status-redraw median=0.013ms
quota-parser median=0.240ms
quota-cold-mock median=0.333ms
quota-warm-mock median=0.234ms
```
