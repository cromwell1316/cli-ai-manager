# H_01 Phase 01 Risk Model And Command Inventory

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Define risk levels and map every command or interactive action to a safety
policy.

## Scope

- Classify read-only, low-risk mutation, credential movement, destructive, and
  external-process actions.
- Inventory `clear`, `sync`, `import`, `export`, `label`, `login`, `launch`,
  service lifecycle, and audit purge.
- Define required flags and prompt text for each risk class.
- Define what must appear in preflight summaries.

## Acceptance

- Every mutating action has an explicit risk class.
- Confirmation behavior is documented before implementation.
- Risk classes are testable.

## Evidence

- Added `cli_profile_manager/safety.py` with risk classes for destructive,
  credential movement, low-risk mutation, and external-process operations.
- Inventory covers `clear`, `sync`, `import`, `export`, `label`, `login`,
  `launch`, service lifecycle, and audit purge/compact.
- `tests/test_profile_manager.py::test_safety_policy_inventory_covers_sensitive_commands`
  verifies inventory coverage and risk assignments.
