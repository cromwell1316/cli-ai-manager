# H_06 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: governance

Status: implemented.

## Boundaries

- Audit must be local-only in this horizon.
- Audit must be privacy-preserving by default.
- Audit must never persist raw tokens, raw credential JSON, auth headers,
  complete native CLI output, or unredacted environment variables.
- Audit must use user-only permissions for files, directories, and SQLite data.
- Audit must remain optional and best-effort by default.
- Strict audit mode may fail commands only when explicitly configured.
- Audit retention and purge behavior must be explicit and documented.

## Review Gates

- Redaction tests must be updated when new event payload fields are added.
- New command handlers must include audit coverage before being accepted.
- Any future remote audit transport requires a separate horizon.
- Any change that stores account identifiers unredacted by default requires an
  explicit privacy review.
