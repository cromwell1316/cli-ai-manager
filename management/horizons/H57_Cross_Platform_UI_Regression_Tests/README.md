# H57 Cross Platform UI Regression Tests

Owner: cli-profile-manager
Source of Truth: management/horizons/H57_Cross_Platform_UI_Regression_Tests/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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

## Files

- `README.md`

