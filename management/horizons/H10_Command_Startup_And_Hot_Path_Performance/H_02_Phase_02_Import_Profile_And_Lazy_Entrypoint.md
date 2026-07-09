# H_02 Phase 02 Import Profile And Lazy Entrypoint

Owner: cli-profile-manager
Source of Truth: management/horizons/H10_Command_Startup_And_Hot_Path_Performance/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Reduce import-time work needed for `--help`, `config show`, and other commands
that do not require quota, credentials, sync, or interactive terminal modules.

## Scope

- Run and record:

```bash
python3 -X importtime profile_manager.py --help
```

- Identify top-level imports that are only needed for specific command groups.
- Move command-specific imports into handlers or focused helper functions.
- Keep compatibility imports from `profile_manager.py` stable where existing
  tests or users rely on them.
- Avoid circular imports while splitting entrypoint responsibilities.

## Acceptance

- Import profile evidence identifies the largest avoidable import costs.
- `--help` and `config show` do not import quota PTY/session code unless needed.
- Existing command JSON contracts and aliases remain unchanged.
