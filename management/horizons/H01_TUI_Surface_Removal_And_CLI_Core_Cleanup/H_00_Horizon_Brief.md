# H_00 Horizon Brief

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: horizon brief

Status: planned.

## Problem

The repository carries a pure keyboard terminal manager and a Textual/Rich TUI
manager. This creates duplicate flows for launching, importing, exporting,
labeling, clearing, and inspecting profiles. The TUI also contradicts the
dependency-free project claim and has platform-specific Windows behavior that is
not present in the WSL CLI path.

## Desired Outcome

Only one local management surface remains: a fast keyboard-first CLI. TUI files,
launch scripts, dependency references, and documentation paths are removed or
explicitly marked obsolete. Profile data and credential files are untouched.

## Success Criteria

- `rg "textual|rich|tui_manager|Start-TUI"` finds no supported runtime path.
- `install.sh` installs only the CLI entrypoint(s).
- `README.md` describes a CLI-only workflow and does not advertise TUI features.
- `python3 -m py_compile profile_manager.py` passes.
- No validation command deletes files under `~/agy-homes`, `~/codex-homes`,
  `~/claude-homes`, or `/mnt/c/Users/*/*-homes`.
