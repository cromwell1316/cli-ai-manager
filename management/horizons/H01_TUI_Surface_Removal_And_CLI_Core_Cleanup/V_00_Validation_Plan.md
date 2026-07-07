# V_00 Validation Plan

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: validation plan

Status: implemented.

## Required Checks

```bash
python3 -m py_compile profile_manager.py
./scripts/verify_no_tui_surface.sh
rg -n "textual|rich|tui_manager|Start-TUI" .
./install.sh
command -v ai-man
command -v pman
```

## Required Assertions

- Any remaining `textual`, `rich`, `tui_manager`, or `Start-TUI` match is either
  inside horizon documentation, explicit implementation evidence, or the guard
  script that checks for reintroduction.
- `install.sh` links only supported CLI entrypoints.
- No protected credential or profile directory is removed.

## Failure Handling

If a TUI reference remains in supported runtime code, remove it. If it remains in
documentation, label it obsolete or delete the claim. Guard self-check strings
are allowed.
