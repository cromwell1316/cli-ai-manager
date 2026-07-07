# H_04 Governance And Safety Boundaries

Owner: cli-profile-manager
Source of Truth: management/horizons/H01_TUI_Surface_Removal_And_CLI_Core_Cleanup/README.md
Lifecycle: living
Document Class: governance

Status: planned.

## Deletion Rules

- Runtime source files can be deleted after inventory.
- Generated caches can be ignored, but not used as deletion evidence.
- OAuth credentials, profile homes, and Windows Credential Manager backups are
  protected data.

## Supported Surface Rule

After this horizon, supported interaction is CLI-only. New TUI code requires a
new horizon and explicit acceptance criteria.

## Honesty Rule

Documentation must not claim zero dependencies if any supported command imports
third-party packages.
