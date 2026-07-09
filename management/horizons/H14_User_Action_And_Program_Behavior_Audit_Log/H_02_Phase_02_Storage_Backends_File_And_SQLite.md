# H_02 Phase 02 Storage Backends File And SQLite

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Implement local audit persistence through a backend abstraction supporting
append-only files and SQLite.

## Scope

- Add an `audit` module with a backend-neutral writer API.
- Store JSONL audit files under the metadata directory by default, with atomic
  append behavior and user-only permissions.
- Store SQLite audit data under the metadata directory by default, using a
  schema suitable for filtered queries by time, event category, command, tool,
  profile, correlation ID, and result status.
- Add safe fallback behavior when the selected backend is unavailable.
- Add explicit corruption handling for truncated JSONL rows and SQLite open or
  migration failures.
- Keep audit writes non-blocking or low-latency enough for hot command paths.

## Acceptance

- File and SQLite backends share the same event contract.
- Audit data is local and user-readable only.
- Backend failures are reported through diagnostics and optional warning events.
- Tests cover successful writes, redaction, backend fallback, and malformed
  persisted data.
