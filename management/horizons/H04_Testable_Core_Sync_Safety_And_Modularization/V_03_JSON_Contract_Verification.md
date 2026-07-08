# V_03 JSON Contract Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H04_Testable_Core_Sync_Safety_And_Modularization/README.md
Lifecycle: living
Document Class: validation

Status: completed.

## Checks

- `status --json` returns the diagnostic status model.
- `import --json` returns success and error payloads.
- `export --json` returns success and error payloads.
- `sync --json` returns the sync report.
- `launch --dry-run --json` returns a launch plan.

## Current Evidence

`status codex bad --json` returns a stable JSON error with `ok: false`, error
type, message, and exit code.

`import codex requirements-dev.txt p1 --dry-run --json` returns a stable success
payload with `ok`, `dry_run`, source, destination, and `would_import`.

`launch codex p1 --dry-run --json` returns a stable launch plan without running
the target CLI.

`sync --from wsl --mode hard --dry-run --json` returns a stable sync report with
`copied`, `skipped`, `converted`, `invalid`, `would_delete`, and `delete_paths`.

`sync --from wsl --mode hard --json` refuses mutation without `--yes` and
returns a stable JSON usage error.

`tests/test_profile_manager.py` verifies import and export dry-run JSON payloads
without writing credentials.
