# H_04 Phase 04 Recovery Diagnostics And Audit

Owner: cli-profile-manager
Source of Truth: management/horizons/H16_Sensitive_Operation_Safety_And_Confirmation_Policy/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make failed or cancelled sensitive operations easy to understand and recover
from.

## Scope

- Add consistent recovery guidance to user-facing errors.
- Include redacted preflight and result summaries in diagnostics.
- Emit audit events for partial completion and rollback limitations.
- Ensure sync and credential movement failures report affected paths safely.

## Acceptance

- Failure messages explain next steps.
- Diagnostics show enough to debug without leaking secrets.
- Audit records distinguish cancellation, preflight failure, partial failure,
  and completed mutation.
