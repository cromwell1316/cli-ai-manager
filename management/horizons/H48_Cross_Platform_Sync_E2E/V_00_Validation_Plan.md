# H48 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Scope

Validate end-to-end WSL and Windows profile sync behavior.

## Checks

- WSL AGY OAuth files convert to Windows `cred-pN.json`.
- Windows `cred-pN.json` files convert to WSL OAuth files.
- Codex, Claude, and metadata sync through soft and hard modes.
- Dry-run reports conversion and deletion plans without writes.

## Commands

```bash
python3 -m pytest tests/test_profile_manager.py -k "sync or windows"
python3 scripts/horizon_governance.py --json
python3 -m pytest
ai-man sync --from wsl --mode soft --dry-run --json
ai-man sync --from windows --mode soft --dry-run --json
```

## Completion Evidence

Validated by deterministic pytest scenarios that use temporary roots through
`AI_MAN_WSL_HOME` and `AI_MAN_WINDOWS_HOME`. Manual `ai-man sync` commands remain
available for local live-root inspection after installation.
