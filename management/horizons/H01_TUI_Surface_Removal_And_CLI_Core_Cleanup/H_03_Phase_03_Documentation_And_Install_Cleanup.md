# H_03 Phase 03 Documentation And Install Cleanup

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: implemented.

## Scope

Make documentation and installation match the CLI-only product.

## Required Changes

- Rewrite README feature claims from TUI to fast keyboard CLI.
- Remove TUI screenshots, menu descriptions, and Textual/Rich references.
- Keep dependency-free claims only if validation proves the runtime is standard
  library only.
- Keep install instructions focused on symlinks to `profile_manager.py`.
- Add a short migration note: old TUI entrypoints are removed; use `ai-man`.

## Phase Exit

A new user following README reaches the supported CLI flow without installing
Textual/Rich or invoking removed launchers.
