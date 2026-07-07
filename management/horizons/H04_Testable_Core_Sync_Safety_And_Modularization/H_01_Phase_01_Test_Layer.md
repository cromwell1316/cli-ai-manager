# H_01 Phase 01 Test Layer

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Scope

Introduce pytest coverage around behavior that currently depends on shell
commands and manual fixtures.

## Required Coverage

- `parse_profile`
- `first_free_profile`
- status detection for agy, codex, and claude
- agy Windows/WSL credential conversion
- import/export atomic replacement behavior
- sync dry-run result shape
- direct-command exit codes and JSON error payloads

## Fixture Boundary

Tests must isolate profile homes with:

```text
AI_MAN_AGY_HOME
AI_MAN_CODEX_HOME
AI_MAN_CLAUDE_HOME
AI_MAN_METADATA_DIR
AI_MAN_WSL_HOME
AI_MAN_WINDOWS_HOME
```

Fixtures must use synthetic credentials only.
