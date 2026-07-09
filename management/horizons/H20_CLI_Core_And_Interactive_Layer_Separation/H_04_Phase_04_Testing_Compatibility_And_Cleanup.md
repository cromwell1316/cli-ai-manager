# H_04 Phase 04 Testing Compatibility And Cleanup

Owner: cli-profile-manager
Source of Truth: management/horizons/H20_CLI_Core_And_Interactive_Layer_Separation/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Verify behavior after migration and remove dead coupling.

## Scope

- Add tests comparing CLI and interactive operation behavior where practical.
- Verify compatibility exports in `profile_manager.py`.
- Remove unused imports and duplicate formatting helpers.
- Update docs for new module boundaries.

## Acceptance

- Full test suite passes.
- Compatibility imports keep working.
- Dead code and duplicate helpers are removed safely.
