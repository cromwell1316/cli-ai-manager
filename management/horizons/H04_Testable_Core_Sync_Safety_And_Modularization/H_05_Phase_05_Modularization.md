# H_05 Phase 05 Modularization

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Scope

Split `profile_manager.py` once tests cover the behavior being moved.

## Extraction Order

1. `paths.py` for profile homes, credential paths, and env-derived roots.
2. `metadata.py` for load/save/labels.
3. `credentials/` modules for agy, codex, and claude.
4. `sync.py` for preflight, copy, conversion orchestration, and reports.
5. `cli.py` for parser and direct-command handlers.
6. `interactive.py` for keyboard menus.

## Acceptance

The installed `profile_manager.py` entrypoint may remain as a compatibility
shim, but core logic must become importable without loading interactive terminal
helpers.
