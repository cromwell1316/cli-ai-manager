# H_02 Phase 02 Cleanup Command And Dry Run

Owner: cli-profile-manager
Source of Truth: management/horizons/H54_Native_Windows_Installer_And_Profile_Cleanup/README.md
Lifecycle: living
Document Class: phase

Status: completed.

## Objective

Provide a safe cleanup workflow for stale profile entries.

## Work

- Add dry-run output that lists proposed edits.
- Require explicit confirmation before mutating profile files.
- Preserve unrelated profile content.

## Exit Criteria

Users can repair stale profile conflicts without manual file surgery.

## Implementation Notes

- Cleanup is dry-run by default.
- Mutating cleanup requires `-Apply -ConfirmCleanup`.
- The script writes `*.ai-man-backup-YYYYMMDD-HHMMSS` before commenting any
  profile lines and preserves unrelated content.
