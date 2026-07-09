# H21 Documentation Governance And Horizon Evidence Automation

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: horizon

Status: completed.

## Purpose

Keep management horizons, validation plans, acceptance matrices, and README
documentation accurate as implementation changes.

## Goals

- Define lifecycle states and required evidence for horizons.
- Add checks for missing horizon files, stale statuses, broken source-of-truth
  links, and incomplete acceptance matrices.
- Tie validation scripts and test commands to horizon evidence.
- Add lightweight release/change notes for completed horizons.
- Keep user-facing README aligned with implemented behavior.

## Non-Goals

- Do not introduce heavyweight project management tooling.
- Do not require external services for documentation validation.
- Do not block experiments on perfect documentation before design is clear.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Horizon_Lifecycle_And_Evidence_Model.md`
- `H_02_Phase_02_Documentation_Consistency_Checks.md`
- `H_03_Phase_03_Validation_Evidence_Automation.md`
- `H_04_Phase_04_Readme_And_Release_Note_Governance.md`
- `H_05_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_Doc_Check_Verification.md`
- `V_02_Evidence_Verification.md`
- `V_03_Acceptance_Matrix.md`
- `V_99_Automated_Evidence.md`

## Completion Notes

- Added `scripts/horizon_governance.py` for deterministic local horizon
  structure validation and sanitized evidence collection.
- Added tests for repository-wide horizon validation and evidence redaction.
- Added README governance instructions and `management/RELEASE_NOTES.md`.
- Verified with `python3 -m pytest -q`: 118 passed.
- Verified `python3 scripts/horizon_governance.py --json`: ok.
