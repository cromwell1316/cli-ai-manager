# H_06 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: governance

Status: completed.

## Secret Handling

Tests and docs must not store real tokens, refresh tokens, API keys, or Windows
Credential Manager exports.

## Windows Boundary

Only explicit Windows activation or Windows launch flows may touch the live
`gemini:antigravity` Credential Manager slot. Dry-run, sync, import, export,
status, and list must not mutate that slot.

## Destructive Sync Boundary

Hard sync must require `--yes` before mutation and must report delete paths
before deleting. Deletion must remain inside the resolved destination home.

## JSON Contract Boundary

Machine-readable commands must return stable success payloads and stable error
payloads with `ok`, `error.type`, `error.message`, and `error.code`.
