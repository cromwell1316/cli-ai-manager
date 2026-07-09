# H_03 Phase 03 CLI And Interactive Migration

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Move CLI commands and interactive workflows to the shared operation layer.

## Scope

- Migrate command handlers to call operation APIs and format results.
- Migrate interactive workflows to call operation APIs and render results.
- Remove broad cross-imports where possible.
- Preserve public CLI behavior and compatibility surface.

## Acceptance

- CLI and interactive paths share core behavior.
- Output remains compatible unless changes are documented.
- Import graph is simpler and tested.

## Evidence

- CLI command handlers call operation APIs for list, status, quota, config,
  import, export, label, clear, sync, audit, and service operations.
- Interactive workflows import profile and credential behavior from
  `cli_profile_manager.operations`.
- Public command behavior is covered by the existing command-surface tests.
