# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 profile_manager.py config show --json
python3 profile_manager.py diagnostics --json
```

## Evidence Requirements

- Registry coverage tests.
- Source precedence tests.
- Redaction tests.
- Diagnostics config health evidence.
