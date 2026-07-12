# H_01 Phase 01 Windows And WSL Install Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document installation, update, verification, and rollback for both platforms.

## Deliverables

- Windows install and verification steps.
- WSL/Linux install and verification steps.
- PATH and execution policy troubleshooting.
- Rollback steps for generated shims and aliases.

## Validation Focus

- A new user can install without external notes.
- Commands match actual scripts and entrypoints.

## Completion Evidence

- `docs/OPERATIONAL_RUNBOOK.md` documents WSL/Linux and native Windows install,
  update, verification, execution policy troubleshooting, PATH troubleshooting,
  temporary Windows validation paths, and rollback.
- README links to the runbook from the top-level introduction.
- Static tests verify install and verification commands remain present.
