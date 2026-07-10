# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H24_AGY_Quota_Tmux_Backend_And_Terminal_Parity/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

Targeted:

```bash
pytest -q tests/test_profile_manager.py -k "agy_quota or tmux or persistent_quota or agy_readiness"
python3 -m py_compile cli_profile_manager/quota.py cli_profile_manager/operations.py cli_profile_manager/config.py
```

Broader quota suite:

```bash
pytest -q tests/test_profile_manager.py -k "quota"
```

Full suite when practical:

```bash
pytest -q
```

If the known performance budget test is unstable, run the full suite excluding
that test and record the exclusion explicitly.

## Manual Validation

Check real AGY profile p1:

```bash
python3 -m cli_profile_manager.cli quota agy p1 --json
```

Check all active AGY profiles through the interactive/status flow that triggered
the original issue.

Check tmux ownership:

```bash
tmux ls
```

Only manager-owned sessions should use the `ai_man_quota_` prefix.

## Evidence Requirements

- Log line showing `backend=tmux`.
- Log line showing `cwd=/home/olivercromwell`.
- Log line showing profile `HOME=/home/olivercromwell/agy-homes/pN`.
- Captured quota state with parsed AGY model percentages.
- No repeated false `auth_required` for token-bearing profiles.
- Cleanup evidence showing manager-owned tmux sessions close or expire.
