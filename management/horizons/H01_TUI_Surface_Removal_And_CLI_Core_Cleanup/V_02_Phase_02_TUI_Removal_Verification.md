# V_02 Phase 02 TUI Removal Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
python3 -m py_compile profile_manager.py
rg -n "from textual|import textual|from rich|import rich|tui_manager|Start-TUI" .
```

## Pass Criteria

- Supported runtime code has no Textual/Rich imports.
- Removed entrypoints cannot be launched from install links.
- CLI entrypoints still compile.
