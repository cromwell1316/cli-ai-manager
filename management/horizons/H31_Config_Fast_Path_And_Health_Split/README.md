# H31 Config Fast Path And Health Split

Owner: cli-profile-manager
Source of Truth: management/horizons/H31_Config_Fast_Path_And_Health_Split/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Make `config show` cheap and deterministic by separating effective settings
from heavier health checks.

## Goals

- Keep effective config resolution fast.
- Move environment health, path existence, and runtime checks into explicit
  health/doctor paths.
- Reuse config registry parsing.
- Preserve current config JSON compatibility where practical.
- Keep warnings for invalid environment values.

## Non-Goals

- Do not remove existing env variable support.
- Do not change defaults.
- Do not make config depend on live CLI availability.

## Work Areas

- Separate pure config resolution from health inspection.
- Cache registry metadata.
- Avoid importing quota, interactive, or diagnostics from config show.
- Add a compatibility shim if existing JSON fields need gradual migration.

## Validation

```bash
python3 scripts/benchmark_runtime.py --scenario commands
pytest -q tests/test_profile_manager.py -k "config"
```

Acceptance target: reduce `config show --json` latency while keeping effective
settings and warnings correct.
