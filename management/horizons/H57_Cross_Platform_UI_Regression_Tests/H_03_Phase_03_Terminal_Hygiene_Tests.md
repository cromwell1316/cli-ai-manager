# H_03 Phase 03 Terminal Hygiene Tests

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Protect shell reset and child CLI theme behavior.

## Work

- Test exit reset behavior.
- Test child CLI theme release before external tools.
- Test Windows no-args startup remains free of Unix terminal imports.

## Exit Criteria

Terminal state regressions are covered by automated tests.

## Implementation Notes

- Existing tests cover exit reset, prompt line erase-to-edge behavior, child CLI
  theme release, renderer cursor restore, non-TTY output, and Windows no-args
  startup without Unix interactive imports.
