# H_01 Phase 01 UI Contract Snapshots

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Define stable UI contract snapshots for cross-platform menus.

## Work

- Capture expected root and tool menu labels.
- Capture symbol shortcuts and hidden legacy aliases.
- Avoid terminal-emulator-specific formatting assertions.

## Exit Criteria

Tests can detect accidental menu label or shortcut drift.

## Implementation Notes

- `interactive_model.contract_snapshot()` captures labels, markers, actions,
  aliases, options, and non-digit shortcut maps.
- Snapshot assertions are ANSI-neutral and avoid terminal-emulator-specific
  rendering details.
