# H_01 Phase 01 End To End Scenario Matrix

Owner: cli-profile-manager
Source of Truth: management/horizons/H22_End_To_End_Operational_Reliability_Sweep/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Define and run realistic workflows across the whole application.

## Scope

- Cover fresh install, profile add/login, import, export, label, clear, sync,
  launch, list, status, quota, config, diagnostics, audit, and service lifecycle.
- Cover JSON and text modes where applicable.
- Cover interactive and noninteractive entry points.
- Track expected state changes and audit events.

## Acceptance

- Scenario matrix covers all major workflows.
- Each scenario has expected outputs and side effects.
- Failures identify owning subsystem.

## Evidence

Validated in a temporary metadata/profile environment:

| Scenario | Evidence |
| --- | --- |
| Config | `config show --json` returned `ok: true` |
| List | `list agy --json` returned 12 visible profiles |
| Status | `status agy p1 --json` and `status codex p1 --json` reported active tokens |
| Import | `import codex <path> p2 --dry-run --json` returned `would_import: true` |
| Export | `export codex p1 --dry-run --json` returned `would_export: true` |
| Sync | `sync --from wsl --mode soft --dry-run --yes --json` returned `ok: true` |
| Audit | `audit list --json --limit 20` returned 20 audit events |
| Runtime service | `service start --json` reported running; `service stop --json` returned `ok: true` |
| Diagnostics | `diagnostics --json` completed successfully in a temporary environment |
