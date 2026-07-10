# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H37_Windows_WSL_Path_Parity_After_Import/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Automated Validation

Targeted path and sync tests:

```bash
pytest -q tests/test_profile_manager.py -k "windows_user or normalize_credential_path or sync"
```

Compile check:

```bash
python3 -m py_compile cli_profile_manager/paths.py cli_profile_manager/sync.py cli_profile_manager/operations.py
```

Full suite:

```bash
pytest -q
```

## Manual Validation

Check WSL dry-run destination:

```bash
python3 -m cli_profile_manager.cli sync --from wsl --mode soft --dry-run --json
```

Expected: `destination_base` resolves to the Windows user that contains the
managed profile roots, or to `AI_MAN_WINDOWS_HOME` when that override is set.
