# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H13_Profile_Process_Resource_Isolation_And_System_Protection/README.md
Lifecycle: living
Document Class: validation

Status: planned.

## Automated Validation

```bash
python3 -m pytest -q
python3 -m py_compile profile_manager.py cli_profile_manager/*.py cli_profile_manager/credentials/*.py scripts/*.py
python3 profile_manager.py config show --json
python3 profile_manager.py diagnostics agy --json
```

## Manual Validation

```bash
python3 profile_manager.py launch agy p1
python3 profile_manager.py quota agy p1 --json
```

## Evidence Requirements

- Capture backend detection for the local host.
- Capture config output showing effective limits.
- Capture diagnostics output showing process policy status.
- Verify fallback behavior without systemd.
