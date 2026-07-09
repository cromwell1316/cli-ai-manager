# H_03 Phase 03 Validation Evidence Automation

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: implementation phase

Status: completed.

## Implementation

`scripts/horizon_governance.py --horizon <path> --evidence --write --json`
runs commands from the horizon validation plan and writes sanitized summaries to
`V_99_Automated_Evidence.md`.

## Objective

Make validation evidence easier to collect and attach to horizon completion.

## Scope

- Add scripts that run horizon-specific validation commands.
- Store summarized evidence in validation docs or implementation evidence files.
- Include test counts, command outputs, benchmark summaries, and diagnostics
  snapshots where appropriate.
- Avoid storing secrets in evidence.

## Acceptance

- Evidence collection can be run locally.
- Evidence redaction is enforced.
- Completed horizons have traceable validation results.
