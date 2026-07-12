# H48 Acceptance Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H48_Cross_Platform_Sync_E2E/README.md
Lifecycle: living
Document Class: validation

Status: planned.

| Area | Acceptance |
|------|------------|
| AGY conversion | Credentials round-trip between Windows backups and WSL OAuth files. |
| Metadata | Account labels and manager metadata sync predictably. |
| Safety | Sync never mutates the live Windows Credential Manager slot. |
| Diagnostics | Dry-run output identifies roots, conversions, skips, and deletes. |
