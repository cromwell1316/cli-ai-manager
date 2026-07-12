# H_02 Phase 02 Action Route Tests

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Verify menu choices dispatch to the expected operations on both platforms.

## Work

- Test launch, login, status, labels, recovery, clear, sync, and settings.
- Keep tests token-safe with fakes and fixtures.
- Ensure credential actions remain in the recovery submenu.

## Exit Criteria

Incorrect action routing fails automated tests before release.

## Implementation Notes

- Route tests cover root menu, WSL tool menu, Windows tool menu, credential sync
  menu, symbol choices, and legacy aliases.
- Existing operation dispatch tests keep credential import/export in the
  recovery submenu rather than the main tool menu.
