# H_01 Phase 01 Boundary Audit And Operation Model

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Define the target separation between parsing, operations, formatting, and
interactive workflow orchestration.

## Scope

- Inventory functions imported across CLI and interactive modules.
- Define operation result envelopes for success, cancellation, validation error,
  not found, no token, and runtime failure.
- Define where audit, safety policy, config, and invalidation hooks live.
- Identify compatibility exports that must remain.

## Acceptance

- Boundary map is documented.
- Operation result model is stable enough for migration.
- Compatibility risks are known.

## Evidence

- `OperationResult` and result constructors are defined in
  `cli_profile_manager.operations`.
- Compatibility exports remain available through `profile_manager.py` and
  `cli_profile_manager.cli`.
- CLI wrappers still own argparse, output formatting, safety decisions, and
  audit event placement.
