# H53 Unified Interactive Renderer For Windows And WSL

Owner: cli-profile-manager
Source of Truth: management/horizons/H53_Unified_Interactive_Renderer_For_Windows_And_WSL/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

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

## Files

- `README.md`

