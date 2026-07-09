# V_01 Event Model Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Validate required event fields for every emitted event.
- Validate event schema versioning.
- Validate correlation ID and parent ID propagation.
- Validate elapsed-time fields for completed events.
- Validate redaction of tokens, credential payloads, accounts, paths, command
  arguments, environment variables, and exception details.

## Evidence

- `test_audit_event_redacts_tokens_accounts_and_paths` validates schema version,
  event IDs, correlation IDs, and default redaction for tokens, accounts, and
  paths.
- Command span events include start and completed terminal events with
  correlation IDs and parent IDs for nested behavior.
- Audit payloads redact secret-like keys and text before persistence.
