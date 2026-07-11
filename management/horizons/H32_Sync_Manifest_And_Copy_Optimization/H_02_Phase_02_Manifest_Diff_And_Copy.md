# H_02 Phase 02 Manifest Diff And Copy

Owner: cli-profile-manager
Source of Truth: management/horizons/H32_Sync_Manifest_And_Copy_Optimization/README.md
Lifecycle: living
Document Class: horizon-phase

Status: implemented.

## Objective

Use manifest diffs to drive copy, skip, conversion, and delete planning.

## Deliverables

- Manifest diff engine.
- Copy decision logic.
- Hard-mode delete preflight from manifest.
- Tests for dry-run and real sync equivalence.

## Result

Copy, skip, and hard-delete decisions are driven from manifest diffs. Soft mode
copies missing, changed-size, or newer source files; hard mode copies only
missing or fact-changed files and removes extra managed destination files.
