# H_03 Phase 03 Recovery Diagnostics And Limitations

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document recovery, diagnostics, and known limitations.

## Deliverables

- Recovery procedures for AGY managed backups.
- Diagnostics examples for all tools.
- Known limitations for Windows AGY quota and concurrent sessions.
- Links to active implementation horizons.

## Validation Focus

- Limitations are accurate and not overstated.
- Troubleshooting steps are actionable.

## Completion Evidence

- Runbook documents `agy-credential whoami`, `restore`, `set`, `save`, and
  `clear` recovery paths with dry-run and confirmation guidance.
- Diagnostics coverage includes `diagnostics`, `config show`, service status,
  audit listing, install verification, CI smoke, and live AGY quota validation.
- Known limitations explicitly cover the shared Windows AGY Credential Manager
  slot, same-user concurrency, native Windows quota behavior, CI token-safety
  scope, and managed sync boundaries.
