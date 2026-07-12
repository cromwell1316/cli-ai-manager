# H53 Unified Interactive Renderer For Windows And WSL

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Unify the interactive application surface so Windows and WSL use the same screen
model, command map, copy, and visual language instead of separate divergent
menus.

## Goals

- Extract shared menu and screen definitions from `interactive.py`.
- Keep platform-specific terminal adapters small and explicit.
- Preserve Windows native safety where raw terminal input differs from WSL.
- Remove duplicated action routing between `interactive.py` and
  `windows_interactive.py`.
- Keep symbol-first navigation consistent on both platforms.

## Non-Goals

- Do not rewrite the operations layer.
- Do not require curses or Unix-only terminal behavior on Windows.
- Do not change credential formats or sync semantics.

## Phases

- Phase 01: inventory current WSL and Windows interactive screens.
- Phase 02: define shared screen/action descriptors and keymaps.
- Phase 03: implement WSL and Windows renderer adapters.
- Phase 04: migrate tool, sync, settings, and credential recovery screens.
- Phase 05: remove duplicated routing and update docs.

## Verification

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 -m pytest
```

Acceptance target: changing a menu label, shortcut, or action route happens in
one shared definition and is reflected on both WSL and native Windows.

## Implementation Evidence

- Added `cli_profile_manager/interactive_model.py` as the shared descriptor
  model for root, tool, credential recovery, and sync menu actions.
- Migrated WSL `interactive.py` root, tool, and credential recovery menus to
  render options and shortcuts from the shared model.
- Migrated native Windows `windows_interactive.py` root, tool, credential
  recovery, and sync menus to the same model while keeping prompt-based Windows
  input isolated from Unix raw terminal handling.
- Added regression coverage proving WSL and Windows tool/recovery menus use the
  shared descriptors and action IDs.

## Completed Validation

```bash
python3 -m pytest tests/test_profile_manager.py -k "interactive or windows_interactive"
python3 scripts/horizon_governance.py --json
python3 -m pytest
```

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Surface_Inventory.md`
- `H_02_Phase_02_Shared_Screen_Model.md`
- `H_03_Phase_03_Platform_Renderer_Adapters.md`
- `H_04_Phase_04_Workflow_Migration.md`
- `H_05_Phase_05_Cleanup_And_Docs.md`
- `README.md`
- `V_00_Validation_Plan.md`
- `V_01_Acceptance_Matrix.md`
- `V_02_Phase_Verification.md`
