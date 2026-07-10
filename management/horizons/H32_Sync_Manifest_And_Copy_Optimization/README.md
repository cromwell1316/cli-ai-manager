# H32 Sync Manifest And Copy Optimization

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: horizon

Status: planned.

## Purpose

Reduce sync cost and make dry-run planning faster without changing what files
are synchronized.

## Goals

- Build explicit manifests for source and destination.
- Avoid unnecessary `os.walk` on known profile directories.
- Compare size and mtime before copying.
- Keep hard sync deletion preflight safe.
- Preserve AGY credential conversion behavior.

## Non-Goals

- Do not sync new file categories.
- Do not remove safety checks for hard mode.
- Do not copy symlinks.

## Work Areas

- Add manifest entries with relative path, size, mtime, and type.
- Reuse profile-specific known file lists for AGY, Codex, Claude, and metadata.
- Use manifest diff for copy/skip/delete decisions.
- Keep dry-run from doing unnecessary credential conversion reads when possible.
- Add timing around large profile roots.

## Validation

```bash
pytest -q tests/test_profile_manager.py -k "sync"
python3 profile_manager.py sync --from wsl --mode soft --dry-run
```

Acceptance target: same sync decisions with less filesystem traversal and faster
dry-run output.
