# H_04 Phase 04 Deterministic Runtime Tests

Owner: cli-profile-manager
Source of Truth: management/horizons/H06_Quota_Runtime_Hardening_And_Recoverability/README.md
Lifecycle: living
Document Class: implementation phase

Status: planned.

## Objective

Make quota runtime behavior testable without real AGY, Codex, or Claude CLIs.

## Scope

- Add fake clock coverage for retry deadlines.
- Add fake session coverage for timeout invalidation and process replacement.
- Add parser fixtures for empty output, auth prompts, changed layout, and valid
  AGY model rows.
- Keep tests fast and independent of local credentials.

## Acceptance

- Runtime tests run inside the normal pytest suite.
- Tests do not require network, real tokens, or installed native CLIs.
- A regression in retry wake-up or session invalidation fails deterministically.
