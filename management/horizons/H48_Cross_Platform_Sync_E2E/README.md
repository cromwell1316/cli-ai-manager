# H48 Cross Platform Sync E2E

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Validate end-to-end profile synchronization between WSL and native Windows for
AGY, Codex, Claude, and metadata.

## Goals

- Prove AGY Windows `cred-pN.json` converts to WSL
  `.gemini/oauth_creds.json`.
- Prove WSL `.gemini/oauth_creds.json` converts back to Windows
  `cred-pN.json`.
- Preserve account metadata during conversion when available.
- Validate soft sync, hard sync, dry-run, and explicit root overrides.
- Add regression tests for Admin-vs-user Windows home detection.

## Non-Goals

- Do not edit the live Windows Credential Manager slot during sync.
- Do not copy unmanaged caches, logs, or large runtime artifacts.
- Do not change existing credential schemas.

## Work Areas

- Build a deterministic fixture matrix for WSL and Windows profile roots.
- Expand sync tests around conversion items, skipped items, and delete plans.
- Add documentation for safe sync direction selection.
- Add diagnostics output that explains source and destination roots.

## Validation

```bash
python3 -m pytest tests/test_profile_manager.py -k "sync or windows"
python3 -m pytest
ai-man sync --from wsl --mode soft --dry-run --json
ai-man sync --from windows --mode soft --dry-run --json
```

Acceptance target: sync can be validated in both directions without touching
the live Windows Credential Manager slot.

## Files

- `README.md`
