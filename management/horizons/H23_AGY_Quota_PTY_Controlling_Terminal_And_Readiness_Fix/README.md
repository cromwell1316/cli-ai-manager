# H23 AGY Quota PTY Controlling Terminal And Readiness Fix

Owner: cli-profile-manager
Source of Truth: management/horizons/H23_AGY_Quota_PTY_Controlling_Terminal_And_Readiness_Fix/README.md
Lifecycle: living
Document Class: horizon

Status: implemented.

## Purpose

Fix AGY quota probing so interactive status screens stop showing `!` for every
AGY account when the native AGY CLI exits or changes process shape during PTY
startup.

## Context

Observed on AGY CLI `1.1.0`: `ai-man quota agy p1 --json` returns
`process_exit` with `CLI process exited during startup`, while direct AGY logs
show `CLI ready for user input`, silent auth, quota refresh, and sometimes
`RESOURCE_EXHAUSTED` or account eligibility errors. Running AGY without a real
TTY also reports Bubble Tea TTY errors.

## Goals

- Launch native AGY quota probes with a real controlling terminal.
- Detect AGY readiness from terminal output instead of relying only on generic
  idle detection.
- Send `/usage` only after AGY is ready to accept slash commands.
- Avoid classifying wrapper-process handoff or early terminal churn as a generic
  startup failure when the CLI produced usable output.
- Improve quota failure diagnostics so `!` can explain `process_exit`,
  `auth_required`, `account_ineligible`, `resource_exhausted`, or parser miss.
- Preserve stale successful quota values during retryable failures.
- Add deterministic fake-CLI tests for TTY-sensitive AGY startup and slash
  command handling.

## Non-Goals

- Do not disable AGY quota probing by default.
- Do not require live AGY accounts or network access in automated tests.
- Do not persist raw PTY buffers, tokens, or unredacted account identifiers.
- Do not rewrite quota parsing for all tools unless a shared helper is required.

## Implementation Summary

- Added a shared quota PTY launcher that assigns the slave PTY as the child
  process controlling terminal before exec.
- Added AGY readiness detection and readiness-gated `/usage` delivery.
- Added AGY-specific failure classification for TTY startup, auth, account
  eligibility, remote resource exhaustion, and local process memory limits.
- Increased AGY startup readiness budget and quota process memory cap to fit
  current AGY CLI startup behavior on WSL without disabling resource policy.
- Added fake CLI regression coverage for `/dev/tty` and readiness-gated command
  delivery.

## Evidence

- `python3 -m pytest -q` -> 122 passed.
- `python3 profile_manager.py quota agy p1 --json --timeout 60` -> `available`
  with AGY model quota limits on the local WSL profile.

## Files

- `H_00_Horizon_Brief.md`
- `H_01_Phase_01_Failure_Reproduction_And_Log_Model.md`
- `H_02_Phase_02_Controlling_TTY_Launcher.md`
- `H_03_Phase_03_AGY_Readiness_And_Command_Delivery.md`
- `H_04_Phase_04_Diagnostics_Stale_Fallback_And_UI_Markers.md`
- `H_05_Phase_05_Fake_CLI_Test_Harness_And_Regression_Coverage.md`
- `H_06_Governance_And_Safety_Boundaries.md`
- `V_00_Validation_Plan.md`
- `V_01_PTY_Launch_Verification.md`
- `V_02_AGY_Probe_Verification.md`
- `V_03_Diagnostics_And_UI_Verification.md`
- `V_04_Acceptance_Matrix.md`
