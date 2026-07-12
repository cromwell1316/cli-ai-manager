# H_03 Phase 03 Update And Rollback

Owner: cli-profile-manager
Source of Truth: management/horizons/H56_Windows_Local_Install_Packaging/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Make Windows-local installs updateable and reversible.

## Work

- Add idempotent update behavior.
- Keep rollback/uninstall from deleting managed profiles.
- Verify stale shims are replaced.

## Exit Criteria

Users can update or rollback the application without losing profiles or tokens.

## Implementation Notes

- Reinstalling backs up the previous app directory as
  `app.rollback-YYYYMMDD-HHMMSS`.
- `-Rollback` restores the latest app backup.
- `-Uninstall` removes app/shims/helper while preserving managed profile and
  credential backup directories.
