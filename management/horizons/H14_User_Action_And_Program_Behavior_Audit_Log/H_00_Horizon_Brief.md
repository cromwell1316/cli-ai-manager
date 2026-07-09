# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H14_User_Action_And_Program_Behavior_Audit_Log/README.md
Lifecycle: living
Document Class: brief

Status: implemented.

## Context

The profile manager can mutate credentials, sync data between WSL and Windows,
launch native CLIs, probe quotas through PTY sessions, and optionally route
commands through a local runtime service. These flows touch sensitive state and
can fail for reasons that are hard to reconstruct after the fact.

## Problem

Current logs are operational and incomplete. They do not provide a consistent
audit trail that answers who initiated an action, which profile/tool was
targeted, which internal decisions were made, what subprocesses were attempted,
what data changed, and how the command ended. Without this trail, debugging,
user support, and safety reviews depend on incomplete terminal output.

## Strategy

Introduce a local audit subsystem with a stable event schema, redaction rules,
correlation IDs, and pluggable storage backends. Instrument command entry
points first, then interactive flows, background quota workers, runtime-service
boundaries, sync decisions, and subprocess launch paths. Expose audit inspection
through CLI commands and keep writes best-effort by default.
