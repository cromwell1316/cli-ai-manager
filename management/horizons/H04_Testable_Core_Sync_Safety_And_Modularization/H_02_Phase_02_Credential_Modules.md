# H_02 Phase 02 Credential Modules

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Scope

Move credential-specific parsing and conversion out of the monolith after the
test layer is active.

## Target Modules

- `credentials/agy.py`: WSL OAuth JSON, Windows backup JSON, BlobBase64
  conversion, account extraction.
- `credentials/codex.py`: `auth.json` validation and account extraction.
- `credentials/claude.py`: `.credentials.json` validation and account summary.

## Acceptance

- Existing import/export/status behavior stays compatible.
- Conversion functions can be tested without invoking CLI parsing or menus.
- No module reads or writes live Windows Credential Manager slots.
