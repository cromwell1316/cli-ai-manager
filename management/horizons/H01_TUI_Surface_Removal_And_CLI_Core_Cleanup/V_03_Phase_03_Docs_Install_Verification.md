# V_03 Phase 03 Docs Install Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase verification

Status: implemented.

## Checks

```bash
rg -n "TUI|Textual|Rich|Start-TUI|zero external dependencies" README.md install.sh
./install.sh
readlink "$HOME/.local/bin/ai-man"
readlink "$HOME/.local/bin/pman"
```

## Pass Criteria

- README and install script describe only supported CLI usage.
- Symlinks point to `profile_manager.py`.
- Dependency-free claims match runtime imports.
