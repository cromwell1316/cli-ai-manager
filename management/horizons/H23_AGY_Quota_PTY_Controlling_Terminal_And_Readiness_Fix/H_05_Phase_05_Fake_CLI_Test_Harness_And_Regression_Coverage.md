# H_05 Phase 05 Fake CLI Test Harness And Regression Coverage

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: implementation phase

Status: implemented.

## Objective

Prove the fix without depending on live AGY accounts or network access.

## Scope

- Add fake CLI fixtures that:
  - require a controlling terminal;
  - emit AGY readiness text;
  - reject early slash commands;
  - return parseable `/usage` output;
  - simulate wrapper process exit;
  - simulate auth required, account ineligible, and resource exhausted output.
- Add tests for persistent and non-persistent quota runner paths.
- Add tests for session invalidation and stale quota preservation.
- Add no-secret checks for diagnostic payloads.

## Acceptance

- Regression tests fail against the old PTY behavior and pass with the fix.
- Tests cover startup success, readiness timeout, slash-command delivery, and
  classified AGY failures.
- The default test suite remains deterministic and does not call live AGY.
