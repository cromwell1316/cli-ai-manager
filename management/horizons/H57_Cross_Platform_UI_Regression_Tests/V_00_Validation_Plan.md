# H57 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Scope

Validate that Windows and WSL UI parity is enforced through automated regression
tests.

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Evidence

- Tests cover root menu symbols and tool menu actions.
- Credential import/export actions stay in the recovery submenu.
- Shell reset and child CLI theme release remain covered.
