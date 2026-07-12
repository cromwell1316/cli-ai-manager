# H57 Cross Platform UI Regression Tests

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Add regression coverage that proves Windows and WSL interactive surfaces stay in
sync as features and design evolve.

## Goals

- Snapshot key menu labels, symbols, and action routes.
- Verify credential actions remain in the recovery submenu.
- Verify shell reset and child CLI theme release behavior.
- Add Windows-native smoke coverage for symbol-first menus.
- Keep tests token-safe and independent of live accounts.

## Non-Goals

- Do not require manual screenshot inspection for every change.
- Do not run live AGY, Codex, or Claude logins in CI.
- Do not encode terminal emulator-specific rendering quirks as product
  requirements.

## Phases

- Phase 01: define UI contract snapshots.
- Phase 02: add shared menu and action-route tests.
- Phase 03: add native Windows smoke assertions.
- Phase 04: integrate into CI and horizon governance.

## Verification

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

Acceptance target: future UI changes cannot silently regress Windows parity,
symbol shortcuts, or credential submenu placement.

## Implementation Evidence

- Added `interactive_model.contract_snapshot()` as a terminal-neutral menu
  contract for root, tool, Windows tool, credential sync, and sync menus.
- Added regression tests for symbol-first labels, hidden legacy digit aliases,
  action-route coverage, and credential submenu placement.
- Added Windows interactive symbol-first snapshot coverage that strips ANSI and
  avoids terminal-emulator-specific assertions.
- Extended `scripts/windows_ci_smoke.ps1` with a focused cross-platform UI
  regression pytest selector.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_UI_Contract_Snapshots.md`
- `H_02_Phase_02_Action_Route_Tests.md`
- `H_03_Phase_03_Terminal_Hygiene_Tests.md`
- `H_04_Phase_04_CI_Integration.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
