# H_02 Phase 02 Effective Settings Command Surface

Owner: cli-profile-manager
Source of Truth: management/horizons/H18_Configuration_Surface_Consolidation_And_Effective_Settings_UX/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Expose effective configuration to users and scripts.

## Scope

- Add or extend `config show` with `--json`, `--sources`, and filtering.
- Show default, environment, metadata, and runtime override sources.
- Add safe text output for common troubleshooting.
- Add config validation output and warnings.

## Acceptance

- Users can see effective values and sources.
- JSON output is stable enough for tests.
- Redacted settings remain redacted in every output mode.
