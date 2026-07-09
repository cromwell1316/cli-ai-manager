# H_01 Phase 01 Audit Event Model And Privacy Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Define the audit event contract, privacy boundaries, redaction rules, and
configuration surface before instrumenting behavior.

## Scope

- Define event categories: `command`, `interactive`, `profile`, `credential`,
  `sync`, `quota`, `runtime_service`, `subprocess`, `config`, `diagnostic`,
  `error`, and `audit`.
- Define event lifecycle names: `started`, `decision`, `attempted`, `succeeded`,
  `failed`, `skipped`, `retried`, and `completed`.
- Add stable fields: event ID, correlation ID, parent ID, timestamp, monotonic
  elapsed time, process ID, command name, tool key, profile number, backend,
  result status, exit code, error class, and redacted details.
- Define payload rules for paths, account identifiers, labels, command
  arguments, native CLI output, quota output, and exception messages.
- Define config keys and environment overrides for enabling audit, backend
  choice, retention, strict mode, account visibility, and path visibility.

## Acceptance

- Event schema is documented and versioned.
- Redaction rules are explicit and testable.
- Audit defaults are privacy-preserving.
- Existing diagnostics can report audit configuration without exposing
  sensitive data.

## Event Schema

Schema version `1` includes `event_id`, `correlation_id`, `parent_id`,
`timestamp`, `monotonic_ms`, `pid`, `category`, `action`, `command`, `tool`,
`profile`, `backend`, `result`, `exit_code`, `error_class`, and redacted
`details`.

## Privacy Defaults

Audit is local and best-effort by default. Tokens, credential-bearing keys,
accounts, paths, raw subprocess output, raw PTY buffers, and environment-like
payloads are redacted unless explicit visibility environment flags are set.
