# V_03 Failure Taxonomy Verification

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: validation

Status: implemented.

## Checks

- Empty output returns `empty_output`.
- Non-empty unmatched output returns `parser_miss`.
- Auth prompt returns `auth_required`.
- Missing CLI returns `missing_cli`.

## Evidence

- `pytest -q` passes with parser coverage for `empty_output`, `parser_miss`,
  `auth_required`, `missing_cli`, and valid AGY quota rows.
