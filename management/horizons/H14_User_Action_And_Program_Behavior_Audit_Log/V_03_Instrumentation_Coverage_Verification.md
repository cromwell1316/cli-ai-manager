# V_03 Instrumentation Coverage Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Verification

- Verify every public command emits start and terminal audit events.
- Verify mutating commands emit decision and result events.
- Verify interactive workflows emit selection, cancellation, confirmation, and
  exit events.
- Verify quota worker, runtime service, sync, and subprocess paths emit
  lifecycle events.
- Verify command failures and exceptions are audited without leaking secrets.

## Evidence

- `test_audit_cli_records_command_and_supports_query_export_purge` verifies
  command start and completed events for public CLI execution.
- CLI instrumentation covers read-only commands, mutating credential/profile
  operations, sync decisions, config reads, runtime-service lifecycle, service
  fallback, subprocess launch attempts, and process policy decisions.
- Interactive instrumentation records menu starts, selections, cancellations,
  status refresh retries, exits, and keyboard interrupts.
- Quota instrumentation records probe attempts, PTY session start/reuse/close,
  process-policy backend decisions, completion states, and failures without
  storing raw screen buffers.
