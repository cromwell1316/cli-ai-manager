# H14 User Action And Program Behavior Audit Log

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Create a complete local audit trail for user actions and program behavior so
operators can understand what happened, when it happened, what changed, and why
a command succeeded or failed.

## Goals

- Record every user-triggered command and interactive workflow transition.
- Record important program behavior: config reads, profile discovery, sync
  decisions, credential import/export attempts, quota probes, runtime-service
  requests, subprocess launch attempts, errors, retries, and recovery paths.
- Store audit data locally through a stable storage abstraction with two
  supported backends: append-only JSONL files and SQLite.
- Keep audit writes best-effort but observable: command success must not depend
  on audit persistence unless strict mode is explicitly enabled.
- Provide a CLI surface to inspect, filter, export, compact, and purge audit
  data.
- Redact tokens, credential payloads, account identifiers by default, command
  arguments that may contain secrets, and filesystem paths when configured.
- Include correlation IDs so one interactive action can be traced across
  command handling, quota workers, sync operations, subprocesses, and runtime
  service calls.
- Add tests proving audit coverage for read-only, mutating, background, and
  failure paths.

## Non-Goals

- Do not send audit data to remote services in this horizon.
- Do not build multi-user centralized compliance reporting.
- Do not persist raw credential files, OAuth refresh tokens, auth headers,
  native CLI screen buffers, or unredacted quota command output.
- Do not make SQLite a required dependency beyond Python's standard `sqlite3`.
- Do not block normal CLI usage on audit write failures unless the user enables
  strict audit mode.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Audit_Event_Model_And_Privacy_Boundaries.md`
- `H_02_Phase_02_Storage_Backends_File_And_SQLite.md`
- `H_03_Phase_03_Command_And_Interactive_Instrumentation.md`
- `H_04_Phase_04_Background_Runtime_And_Subprocess_Instrumentation.md`
- `H_05_Phase_05_Audit_Query_Export_And_Retention.md`
- `H_06_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Event_Model_Verification.md`
- `V_02_Storage_Backend_Verification.md`
- `V_03_Instrumentation_Coverage_Verification.md`
- `V_04_Query_Retention_Verification.md`
- `V_05_Acceptance_Matrix.md`
