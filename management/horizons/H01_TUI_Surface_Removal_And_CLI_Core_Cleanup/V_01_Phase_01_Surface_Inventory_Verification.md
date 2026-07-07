# V_01 Phase 01 Surface Inventory Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase verification

Status: planned.

## Checks

```bash
find . /mnt/c/Users/Oliver/ai-man-tui-win -maxdepth 3 -type f | sort
rg -n "textual|rich|tui_manager|Start-TUI|TUI" . /mnt/c/Users/Oliver/ai-man-tui-win
```

## Pass Criteria

- Removable files are listed.
- Protected profile homes and credential files are excluded from removal.
- The owner can identify every supported TUI entrypoint before Phase 02.
