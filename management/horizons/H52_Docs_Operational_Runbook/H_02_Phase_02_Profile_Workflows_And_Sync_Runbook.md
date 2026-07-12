# H_02 Phase 02 Profile Workflows And Sync Runbook

Owner: cli-profile-manager
Source of Truth: management/horizons/H52_Docs_Operational_Runbook/README.md
Lifecycle: living
Document Class: horizon-phase

Status: completed.

## Objective

Document day-to-day profile workflows and sync behavior.

## Deliverables

- First-login flows for AGY, Codex, and Claude.
- AGY Windows Credential Manager model explanation.
- Import/export examples.
- Sync direction examples and dry-run guidance.

## Validation Focus

- Credential authority differences are explicit.
- Examples avoid real account names and tokens.

## Completion Evidence

- Runbook documents AGY WSL OAuth files, Windows `cred-pN.json` backups, and the
  native Windows `gemini:antigravity` live slot.
- First-login examples cover `agy`, `codex`, `claude`, and AGY `p1`, `p2`, `p3`.
- Import, export, launch, quota/status, diagnostics, sync soft/hard, dry-run, and
  explicit root override examples are included without raw tokens.
