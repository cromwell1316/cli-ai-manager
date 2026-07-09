# H_02 Phase 02 Core Service Extraction

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Extract reusable operation APIs from CLI-oriented code.

## Scope

- Add core operation modules for profile status, credential movement, sync,
  quota, config, runtime service, and audit.
- Keep formatting outside operation modules.
- Keep filesystem and process side effects explicit.
- Add unit tests for operations without CLI parsing.

## Acceptance

- Core operations can be called from CLI and interactive code.
- Operation modules avoid direct terminal rendering.
- Tests cover operation results independently of argparse.

## Evidence

- `cli_profile_manager.operations` contains operation APIs for profile status,
  list, quota, import, export, label, clear, sync, config, audit, runtime
  service, and launch preparation.
- The operation module does not import terminal rendering or interactive UI.
- Quota dependencies are lazy-loaded so config/help hot paths do not import the
  quota module.
