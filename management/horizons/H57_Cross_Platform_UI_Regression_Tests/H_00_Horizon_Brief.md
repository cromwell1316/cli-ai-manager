# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: brief

Status: completed.

## Context

UI regressions have appeared when Windows and WSL surfaces were updated
separately.

## Problem

Manual screenshots catch issues late and do not prevent route or shortcut drift.

## Strategy

Codify the cross-platform UI contract in automated tests for labels, shortcuts,
routes, and terminal hygiene.

## Expected Result

Future UI changes fail tests when Windows and WSL diverge unexpectedly.
