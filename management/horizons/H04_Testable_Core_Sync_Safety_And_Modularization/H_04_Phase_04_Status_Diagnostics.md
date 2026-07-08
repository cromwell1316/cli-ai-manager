# H_04 Phase 04 Status Diagnostics

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Scope

Replace ambiguous token presence reporting with a stable diagnostic model.

## JSON Model

```json
{
  "has_token": true,
  "token_state": "valid",
  "credential_source": "wsl-oauth",
  "account": "user@example.com",
  "warnings": []
}
```

`token_state` values are `valid`, `missing`, `invalid`, and `unsupported`.
`credential_source` values include `wsl-oauth`, `agy-cli-token`,
`windows-backup`, `codex-auth`, and `claude-credentials`.

## Acceptance

Text rendering may stay compact, but JSON output must preserve the complete
diagnostic payload.
