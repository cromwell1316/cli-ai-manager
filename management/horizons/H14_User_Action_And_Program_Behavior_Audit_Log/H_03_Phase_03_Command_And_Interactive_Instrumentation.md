# H_03 Phase 03 Command And Interactive Instrumentation

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Instrument user-facing command execution and interactive workflows with
complete audit events.

## Scope

- Emit command start and completion events for all noninteractive commands.
- Emit workflow events for interactive menu selection, profile selection,
  confirmation prompts, cancelled actions, and exits.
- Capture mutating operations: label changes, clear operations, import/export,
  login/add profile, sync direction and mode, and launch attempts.
- Capture read-only operations: list, status, quota, config, diagnostics, and
  service status.
- Use correlation IDs so a single user action can be followed across helper
  functions and nested operations.
- Record affected profile/tool metadata without writing raw credentials.

## Acceptance

- Every CLI command emits a start and terminal event.
- Mutating commands include precondition, decision, and result events.
- Interactive workflows can be reconstructed from audit events.
- Tests prove cancellation and failure paths are audited.
