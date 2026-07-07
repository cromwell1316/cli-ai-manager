# V_06 Implementation Evidence

Owner: cli-profile-manager
Source of Truth: management/horizons/H02_Keyboard_First_Profile_Command_Surface/README.md
Lifecycle: living
Document Class: implementation evidence

Status: implemented.

## Evidence Log

- Added `argparse` command surface:
  `list`, `status`, `launch`, `login`/`add`, `import`, `export`, `label`,
  `clear`, and `sync`.
- Added `--json` output for `list` and `status`.
- Split occupied profile discovery from display slots.
- Added first-free profile selection for login/import defaults.
- Added `AI_MAN_AGY_HOME`, `AI_MAN_CODEX_HOME`, `AI_MAN_CLAUDE_HOME`, and
  `AI_MAN_METADATA_DIR` fixture overrides.
- Added stable non-zero exit codes for invalid profiles, missing files,
  missing token, missing executable, and runtime failures.
- Updated the interactive selector with digit selection and H02 shortcuts.
- Routed interactive launch, login, import, export, label, and clear through
  the same backend functions used by direct commands.
- Updated `README.md` with command grammar, keymap, and exit codes.

Validation passed:

- `python3 -m py_compile profile_manager.py`
- `python3 profile_manager.py --help`
- `python3 profile_manager.py list --help`
- `python3 profile_manager.py launch --help`
- `python3 profile_manager.py sync --help`
- `python3 profile_manager.py list agy --json`
- `python3 profile_manager.py list codex --json`
- `python3 profile_manager.py list claude --json`
- empty temporary `AI_MAN_AGY_HOME` returns `next_profile: p1`
- temporary `AI_MAN_AGY_HOME` with `p1` and `p3` returns `next_profile: p2`
- temporary `AI_MAN_CODEX_HOME` with `p1` and `p3` imports into `p2`
- `python3 profile_manager.py status agy p0` exits `2`
- empty temporary `launch agy p1` exits `4`
- missing import source exits `3`
- `./scripts/verify_no_tui_surface.sh`

## Residuals

Credential model corrections remain owned by H03.
