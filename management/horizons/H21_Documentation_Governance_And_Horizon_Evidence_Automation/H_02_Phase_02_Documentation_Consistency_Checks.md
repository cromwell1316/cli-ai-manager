# H_02 Phase 02 Documentation Consistency Checks

Owner: cli-profile-manager
Source of Truth: management/horizons/H21_Documentation_Governance_And_Horizon_Evidence_Automation/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Add automated checks for horizon document integrity.

## Scope

- Check required files exist.
- Check `Source of Truth` paths point to existing README files.
- Check status values are recognized.
- Check acceptance matrices are present and non-empty.
- Check validation plans include executable commands where relevant.

## Acceptance

- A local script can validate horizon structure.
- CI or manual verification can run the same script.
- Failures give actionable messages.
