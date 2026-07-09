# H_03 Phase 03 AGY Readiness And Command Delivery

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Send AGY quota slash commands only after the native CLI is ready.

## Scope

- Add AGY-specific readiness matcher for `CLI ready for user input`, stable
  prompt output, and completed silent-auth churn.
- Replace generic startup idle wait for AGY with readiness-or-failure wait.
- Continue using generic idle wait for Codex and Claude unless tests require a
  shared abstraction.
- Ensure `/usage` is sent as a slash command, not interpreted as a model prompt.
- Tune startup and post-command waits for AGY without relying on long sleeps.
- Capture enough sanitized output for parser and diagnostics.

## Acceptance

- Fake AGY CLI receives `/usage` only after readiness marker.
- Startup wrapper churn does not become `process_exit` if the PTY remains usable.
- Slash command output can be parsed into quota limits.
